"""
Versioned Eligibility Rules Endpoints.
Implements Hackathon Challenge 04: Rules That Change.
Admins can publish new eligibility rule sets dynamically with zero downtime and no redeployment.
All old decisions retain their historical rule version.
"""
from typing import List

from fastapi import APIRouter, Depends, status

from services.api.engine.audit_log import audit_log
from services.api.engine.rules_engine import rules_engine
from services.api.security.rbac import get_current_user, require_admin
from services.shared.schemas import RuleSet, RuleVersionResponse, UserResponse

router = APIRouter(prefix="/rules", tags=["Versioned Rules Engine"])


@router.get("/active", response_model=RuleSet)
async def get_active_rules():
    """Returns currently active eligibility rule set."""
    return rules_engine.get_active_rules()


@router.get("/versions", response_model=List[RuleVersionResponse])
async def list_rule_versions(current_user: UserResponse = Depends(get_current_user)):
    """Returns history of all immutable rule versions."""
    versions = rules_engine.list_all_versions()
    return [
        RuleVersionResponse(
            version=r.version,
            name=r.name,
            is_active=r.is_active,
            rule_set=r,
            created_at=r.created_at
        )
        for r in versions
    ]


@router.post("/publish", response_model=RuleSet, status_code=status.HTTP_201_CREATED)
async def publish_rule_version(
    draft_rules: RuleSet,
    current_user: UserResponse = Depends(require_admin)
):
    """
    Admin publishes a new rule set.
    Becomes active immediately without code changes or server restart.
    """
    published = rules_engine.publish_new_version(
        draft=draft_rules,
        publisher_id=current_user.id
    )

    audit_log.append(
        actor_id=current_user.id,
        actor_role=current_user.role,
        action="RULE_VERSION_PUBLISHED",
        resource_id=f"rule_v{published.version}",
        details={
            "version": published.version,
            "name": published.name,
            "max_monthly_income": published.max_monthly_income,
            "max_auto_approve_amount": published.max_auto_approve_amount
        }
    )

    return published
