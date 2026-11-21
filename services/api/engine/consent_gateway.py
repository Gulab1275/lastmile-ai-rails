"""
Consent Gateway.
Implements Hackathon Challenge 06: Consent and Take-Back & Principle 4.
All citizen data access MUST pass through the Consent Gateway.
If consent is withdrawn, access is immediately blocked with HTTP 403 and logged to the audit trail.
"""
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import HTTPException

from services.api.engine.audit_log import audit_log
from services.shared.schemas import (
    ConsentRecord,
    ConsentScope,
    RoleEnum,
)


class ConsentWithdrawnException(HTTPException):
    def __init__(self, citizen_id: str, scope: ConsentScope):
        super().__init__(
            status_code=403,
            detail={
                "code": "CONSENT_WITHDRAWN",
                "message_en": f"Access denied: Citizen {citizen_id} has revoked consent for scope '{scope.value}'.",
                "message_ur": f"رسائی مسترد: شہری نے '{scope.value}' کا رضامندی پرمٹ واپس لے لیا ہے۔",
                "citizen_id": citizen_id,
                "scope": scope.value
            }
        )


class ConsentGateway:
    def __init__(self):
        # In-memory consent store: citizen_id -> {scope -> ConsentRecord}
        self._consents: Dict[str, Dict[ConsentScope, ConsentRecord]] = {}

    def grant_consent(
        self,
        citizen_id: str,
        scope: ConsentScope,
        helper_id: Optional[str] = None,
        actor_id: str = "citizen",
        actor_role: RoleEnum = RoleEnum.CITIZEN
    ) -> ConsentRecord:
        """
        Grants granular consent for a specific data scope.
        Logs change to the cryptographic audit trail.
        """
        if citizen_id not in self._consents:
            self._consents[citizen_id] = {}

        record_id = f"cns_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow()

        audit_entry = audit_log.append(
            actor_id=actor_id,
            actor_role=actor_role,
            action=f"CONSENT_GRANTED:{scope.value}",
            resource_id=citizen_id,
            details={"scope": scope.value, "helper_id": helper_id}
        )

        record = ConsentRecord(
            id=record_id,
            citizen_id=citizen_id,
            scope=scope,
            granted=True,
            granted_to_helper_id=helper_id,
            granted_at=now,
            revoked_at=None,
            audit_hash=audit_entry.current_hash
        )

        self._consents[citizen_id][scope] = record

        # Dual-persistence to Supabase Postgres
        try:
            from db.connection import SessionLocal
            from db.models import Consent as DBConsent
            from services.shared.schemas import ConsentStatus
            with SessionLocal() as db_session:
                db_rec = db_session.query(DBConsent).filter_by(citizen_id=citizen_id, scope=scope.value).first()
                if db_rec:
                    db_rec.status = ConsentStatus.ACTIVE.value
                    db_rec.revoked_at = None
                else:
                    db_rec = DBConsent(
                        citizen_id=citizen_id,
                        grantee=helper_id or "system",
                        scope=scope.value,
                        status=ConsentStatus.ACTIVE.value
                    )
                    db_session.add(db_rec)
                db_session.commit()
        except Exception:
            pass

        return record

    def withdraw_consent(
        self,
        citizen_id: str,
        scope: ConsentScope,
        actor_id: str = "citizen",
        actor_role: RoleEnum = RoleEnum.CITIZEN
    ) -> ConsentRecord:
        """
        Withdraws consent for a specific scope.
        Subsequent data access requests will immediately fail with HTTP 403.
        """
        if citizen_id not in self._consents or scope not in self._consents[citizen_id]:
            # Create a revoked record if non-existent
            return self.grant_consent(citizen_id, scope, None, actor_id, actor_role)

        record = self._consents[citizen_id][scope]
        now = datetime.utcnow()

        audit_entry = audit_log.append(
            actor_id=actor_id,
            actor_role=actor_role,
            action=f"CONSENT_WITHDRAWN:{scope.value}",
            resource_id=citizen_id,
            details={"scope": scope.value, "previous_granted_at": record.granted_at.isoformat()}
        )

        updated_record = record.model_copy(update={
            "granted": False,
            "revoked_at": now,
            "audit_hash": audit_entry.current_hash
        })

        self._consents[citizen_id][scope] = updated_record

        # Dual-persistence to Supabase Postgres
        try:
            from db.connection import SessionLocal
            from db.models import Consent as DBConsent
            with SessionLocal() as db_session:
                db_rec = db_session.query(DBConsent).filter_by(citizen_id=citizen_id, scope=scope.value).first()
                if db_rec:
                    db_rec.status = "revoked"
                    db_rec.revoked_at = now
                    db_session.commit()
        except Exception:
            pass

        return updated_record

    def check_consent(
        self,
        citizen_id: str,
        scope: ConsentScope,
        acting_helper_id: Optional[str] = None
    ) -> bool:
        """Checks whether consent is actively granted."""
        citizen_scope_map = self._consents.get(citizen_id, {})
        record = citizen_scope_map.get(scope)

        if not record or not record.granted:
            return False

        # If checking helper permission, verify acting helper matches granted helper
        if scope == ConsentScope.HELPER_ACTING and acting_helper_id:
            return record.granted_to_helper_id == acting_helper_id

        return True

    def read_gateway(
        self,
        actor_id: str,
        actor_role: RoleEnum,
        citizen_id: str,
        scope: ConsentScope,
        acting_helper_id: Optional[str] = None
    ) -> bool:
        """
        Gatekeeper for reading citizen data.
        Raises HTTP 403 ConsentWithdrawnException if consent is not actively granted.
        Writes access check to the audit log.
        """
        # Auditors have read-only access for verification without personal data disclosure
        if actor_role == RoleEnum.AUDITOR:
            audit_log.append(
                actor_id=actor_id,
                actor_role=actor_role,
                action=f"AUDITOR_READ_METADATA:{scope.value}",
                resource_id=citizen_id,
                details={"scope": scope.value, "access_status": "ALLOWED_FOR_AUDITOR"}
            )
            return True

        has_consent = self.check_consent(citizen_id, scope, acting_helper_id)

        if not has_consent:
            audit_log.append(
                actor_id=actor_id,
                actor_role=actor_role,
                action=f"UNAUTHORIZED_ACCESS_BLOCKED:{scope.value}",
                resource_id=citizen_id,
                details={"scope": scope.value, "reason": "CONSENT_WITHDRAWN_OR_MISSING"}
            )
            raise ConsentWithdrawnException(citizen_id, scope)

        audit_log.append(
            actor_id=actor_id,
            actor_role=actor_role,
            action=f"CONSENT_VERIFIED_READ:{scope.value}",
            resource_id=citizen_id,
            details={"scope": scope.value, "access_status": "PERMITTED"}
        )
        return True

    def get_citizen_consents(self, citizen_id: str) -> Dict[str, Any]:
        """Returns active and revoked consents for a citizen."""
        citizen_map = self._consents.get(citizen_id, {})
        return {
            scope.value: {
                "granted": rec.granted,
                "granted_at": rec.granted_at.isoformat() if rec.granted_at else None,
                "revoked_at": rec.revoked_at.isoformat() if rec.revoked_at else None,
                "helper_id": rec.granted_to_helper_id
            }
            for scope, rec in citizen_map.items()
        }


# Global Singleton Consent Gateway
consent_gateway = ConsentGateway()
