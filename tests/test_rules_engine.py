"""
Tests for Versioned Rules Engine.
Implements Challenge 04: Rules That Change.
Verifies condition firing traces and dynamic version publishing without redeployment.
"""
from services.api.engine.rules_engine import RulesEngine
from services.shared.schemas import RuleSet


def test_rules_engine_baseline_evaluation():
    engine = RulesEngine()
    case_eligible = {
        "monthly_income": 25000.0,
        "household_size": 4,
        "requested_amount": 12000.0
    }
    trace = engine.evaluate(case_eligible)
    assert trace.passed_all is True
    assert len(trace.failed_conditions) == 0


def test_rules_engine_failing_income_condition():
    engine = RulesEngine()
    case_ineligible = {
        "monthly_income": 45000.0,  # Exceeds max 35000
        "household_size": 2,
        "requested_amount": 10000.0
    }
    trace = engine.evaluate(case_ineligible)
    assert trace.passed_all is False
    assert any("exceeds threshold" in f for f in trace.failed_conditions)


def test_rules_engine_publish_new_version():
    """
    Verifies that publishing a new rule version:
    1. Increments version number
    2. Becomes active immediately
    3. Old decisions can still reference their historical version
    """
    engine = RulesEngine()
    v1 = engine.get_active_rules()
    assert v1.version == 1

    draft = RuleSet(
        version=2,
        name="Emergency Flood Relief v2.0",
        max_monthly_income=50000.0,  # Raised threshold
        min_household_size=2,
        max_auto_approve_amount=20000.0
    )

    new_rule = engine.publish_new_version(draft, publisher_id="test_admin")
    assert new_rule.version == 2
    assert engine.get_active_rules().version == 2

    # A case with 45k income fails under v1 but passes under v2!
    case_data = {"monthly_income": 45000.0, "household_size": 3, "requested_amount": 15000.0}
    trace_v1 = engine.evaluate(case_data, version=1)
    trace_v2 = engine.evaluate(case_data, version=2)

    assert trace_v1.passed_all is False
    assert trace_v2.passed_all is True
