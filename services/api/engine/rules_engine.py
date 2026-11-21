"""
Versioned Rules Engine.
Allows non-technical admins to update eligibility rules dynamically without code changes or server redeployment.
Old decisions preserve their historical rule version for full auditability.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from services.shared.schemas import RuleCondition, RuleEvaluationTrace, RuleSet

# Default Genesis Rule Set (Version 1)
DEFAULT_V1_RULESET = RuleSet(
    version=1,
    name="National Relief Grant Baseline v1.0",
    max_monthly_income=35000.0,
    min_household_size=1,
    max_auto_approve_amount=15000.0,
    requires_valid_cnic=True,
    requires_utility_bill=True,
    max_wrong_prob_auto_approve=0.05,
    max_wrong_prob_ask_proof=0.30,
    custom_conditions=[
        RuleCondition(
            field="monthly_income",
            operator="lte",
            value=35000.0,
            description_en="Monthly household income must be PKR 35,000 or below.",
            description_ur="ماہانہ گھریلو آمدنی 35,000 روپے یا اس سے کم ہونی چاہیے۔"
        ),
        RuleCondition(
            field="requested_amount",
            operator="lte",
            value=25000.0,
            description_en="Requested relief amount must not exceed cap of PKR 25,000.",
            description_ur="امداد کی مطلوبہ رقم 25,000 روپے کی حد سے زیادہ نہیں ہونی چاہیے۔"
        )
    ],
    created_by="admin_system",
    created_at=datetime.utcnow(),
    is_active=True
)


class RulesEngine:
    def __init__(self):
        # In-memory storage of immutable rule versions
        self._rule_versions: Dict[int, RuleSet] = {1: DEFAULT_V1_RULESET}
        self._active_version: int = 1

    def get_active_rules(self) -> RuleSet:
        return self._rule_versions[self._active_version]

    def get_rule_by_version(self, version: int) -> Optional[RuleSet]:
        return self._rule_versions.get(version)

    def list_all_versions(self) -> List[RuleSet]:
        return sorted(self._rule_versions.values(), key=lambda r: r.version)

    def publish_new_version(self, draft: RuleSet, publisher_id: str = "admin") -> RuleSet:
        """
        Publishes a new immutable rule version and sets it as active immediately.
        No redeployment or server restart required.
        """
        new_version_num = max(self._rule_versions.keys()) + 1
        new_ruleset = draft.model_copy(update={
            "version": new_version_num,
            "created_by": publisher_id,
            "created_at": datetime.utcnow(),
            "is_active": True
        })

        # Deactivate previous active version
        if self._active_version in self._rule_versions:
            self._rule_versions[self._active_version] = self._rule_versions[self._active_version].model_copy(
                update={"is_active": False}
            )

        self._rule_versions[new_version_num] = new_ruleset
        self._active_version = new_version_num

        # Dual-persistence to Supabase Postgres
        try:
            from db.connection import SessionLocal
            from db.models import RuleVersion as DBRuleVersion
            with SessionLocal() as db_session:
                db_rule = DBRuleVersion(
                    version=new_version_num,
                    rule_name=new_ruleset.name,
                    conditions=[c.model_dump() if hasattr(c, "model_dump") else c.__dict__ for c in new_ruleset.custom_conditions],
                    author=publisher_id,
                    status="active"
                )
                db_session.add(db_rule)
                db_session.commit()
        except Exception:
            pass

        return new_ruleset

    def evaluate_condition(self, case_data: Dict[str, Any], condition: RuleCondition) -> Dict[str, Any]:
        """Evaluates a single condition against case data."""
        actual_value = case_data.get(condition.field)
        passed = False

        if actual_value is not None:
            if condition.operator == "lte":
                passed = float(actual_value) <= float(condition.value)
            elif condition.operator == "gte":
                passed = float(actual_value) >= float(condition.value)
            elif condition.operator == "eq":
                passed = str(actual_value).strip().lower() == str(condition.value).strip().lower()
            elif condition.operator == "ne":
                passed = str(actual_value) != str(condition.value)
            elif condition.operator == "in":
                passed = actual_value in condition.value
            elif condition.operator == "not_in":
                passed = actual_value not in condition.value

        return {
            "field": condition.field,
            "operator": condition.operator,
            "required_value": condition.value,
            "actual_value": actual_value,
            "passed": passed,
            "description_en": condition.description_en,
            "description_ur": condition.description_ur
        }

    def evaluate(self, case_data: Dict[str, Any], version: Optional[int] = None) -> RuleEvaluationTrace:
        """
        Evaluates a case against a specific rule version (or the currently active version).
        Returns a complete condition firing trace for explainability and auditing.
        """
        rule_set = self.get_rule_by_version(version) if version else self.get_active_rules()
        if not rule_set:
            rule_set = self.get_active_rules()

        condition_results = []
        failed_conditions = []

        # 1. Base Built-in Rule Checks
        income = float(case_data.get("monthly_income", 0.0))
        income_passed = income <= rule_set.max_monthly_income
        condition_results.append({
            "field": "monthly_income",
            "operator": "lte",
            "required_value": rule_set.max_monthly_income,
            "actual_value": income,
            "passed": income_passed,
            "description_en": f"Income must be <= {rule_set.max_monthly_income}",
            "description_ur": f"آمدنی {rule_set.max_monthly_income} سے کم یا برابر ہونی چاہیے۔"
        })
        if not income_passed:
            failed_conditions.append(f"Income ({income}) exceeds threshold ({rule_set.max_monthly_income})")

        household_size = int(case_data.get("household_size", 1))
        household_passed = household_size >= rule_set.min_household_size
        condition_results.append({
            "field": "household_size",
            "operator": "gte",
            "required_value": rule_set.min_household_size,
            "actual_value": household_size,
            "passed": household_passed,
            "description_en": f"Household size must be >= {rule_set.min_household_size}",
            "description_ur": f"افراد خانہ کی تعداد کم از کم {rule_set.min_household_size} ہونی چاہیے۔"
        })
        if not household_passed:
            failed_conditions.append(f"Household size ({household_size}) below minimum")

        # 2. Custom Condition Checks
        for cond in rule_set.custom_conditions:
            res = self.evaluate_condition(case_data, cond)
            condition_results.append(res)
            if not res["passed"]:
                failed_conditions.append(res["description_en"])

        passed_all = len(failed_conditions) == 0

        return RuleEvaluationTrace(
            rule_name=rule_set.name,
            rule_version=rule_set.version,
            condition_results=condition_results,
            passed_all=passed_all,
            failed_conditions=failed_conditions
        )


# Global Singleton Rules Engine
rules_engine = RulesEngine()
