"""
Consent Gateway.
Implements Hackathon Challenge 06: Consent and Take-Back & Principle 4.
All citizen data access MUST pass through the Consent Gateway.
If consent is withdrawn, access is immediately blocked with HTTP 403 and logged to the audit trail.
Enhanced in Production Security Hardening Mission 2:
- PostgreSQL persistent storage is the authoritative consent source.
- Immediate visibility across multi-worker processes.
- Database transactions with row-level locks prevent race conditions.
- Fails closed upon database connection failures.
- Zero stale cached consent overrides database state.
"""
import uuid
import threading
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import HTTPException

from services.api.engine.audit_log import audit_log
from services.shared.schemas import (
    ConsentRecord,
    ConsentScope,
    RoleEnum,
    ConsentStatus,
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


def _ensure_citizen_record(db_session, citizen_id: str):
    """Ensures a corresponding citizen record exists to satisfy foreign key constraints."""
    from db.models import Citizen as DBCitizen
    citizen = db_session.query(DBCitizen).filter_by(id=citizen_id).first()
    if not citizen:
        safe_hash = abs(hash(citizen_id)) % 10000000
        safe_cnic = f"99999-{safe_hash:07d}-1"
        existing = db_session.query(DBCitizen).filter_by(cnic=safe_cnic).first()
        if existing and existing.id != citizen_id:
            safe_cnic = f"99998-{safe_hash:07d}-2"
        citizen = DBCitizen(
            id=citizen_id,
            cnic=safe_cnic,
            full_name=f"Citizen {citizen_id}"
        )
        db_session.add(citizen)
        db_session.flush()
    return citizen


class ConsentGateway:
    def __init__(self):
        # Process-local cache synced with PostgreSQL: citizen_id -> {scope -> ConsentRecord}
        self._consents: Dict[str, Dict[ConsentScope, ConsentRecord]] = {}
        self._lock = threading.RLock()

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
        Persists to PostgreSQL authoritative store with database transaction.
        Logs change to the cryptographic audit trail.
        """
        with self._lock:
            record_id = f"cns_{uuid.uuid4().hex[:12]}"
            now = datetime.utcnow()

            # Authoritative persistent store: PostgreSQL with transaction & row-level locking
            try:
                from db.connection import SessionLocal
                from db.models import Consent as DBConsent
                with SessionLocal() as db_session:
                    _ensure_citizen_record(db_session, citizen_id)
                    db_rec = db_session.query(DBConsent).filter_by(
                        citizen_id=citizen_id, scope=scope.value
                    ).with_for_update().first()

                    if db_rec:
                        db_rec.status = ConsentStatus.ACTIVE.value
                        db_rec.grantee = helper_id or "system"
                        db_rec.granted_at = now
                        db_rec.revoked_at = None
                    else:
                        db_rec = DBConsent(
                            id=record_id,
                            citizen_id=citizen_id,
                            grantee=helper_id or "system",
                            scope=scope.value,
                            status=ConsentStatus.ACTIVE.value,
                            granted_at=now,
                            revoked_at=None
                        )
                        db_session.add(db_rec)
                    db_session.commit()
            except Exception as e:
                # Requirement 7: Fail closed on database failure
                raise HTTPException(status_code=503, detail=f"Consent persistence failure: database unavailable ({str(e)})")

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

            if citizen_id not in self._consents:
                self._consents[citizen_id] = {}
            self._consents[citizen_id][scope] = record

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
        Persists revocation to PostgreSQL authoritative store with database transaction.
        Subsequent data access requests immediately fail across all API workers.
        """
        with self._lock:
            now = datetime.utcnow()
            record_id = f"cns_rev_{uuid.uuid4().hex[:12]}"
            prev_granted_at = None

            # Authoritative persistent store: PostgreSQL with transaction & row-level locking
            try:
                from db.connection import SessionLocal
                from db.models import Consent as DBConsent
                with SessionLocal() as db_session:
                    _ensure_citizen_record(db_session, citizen_id)
                    db_rec = db_session.query(DBConsent).filter_by(
                        citizen_id=citizen_id, scope=scope.value
                    ).with_for_update().first()

                    if db_rec:
                        prev_granted_at = db_rec.granted_at.isoformat() if db_rec.granted_at else None
                        db_rec.status = "revoked"
                        db_rec.revoked_at = now
                    else:
                        db_rec = DBConsent(
                            id=record_id,
                            citizen_id=citizen_id,
                            grantee="system",
                            scope=scope.value,
                            status="revoked",
                            granted_at=now,
                            revoked_at=now
                        )
                        db_session.add(db_rec)
                    db_session.commit()
            except Exception as e:
                # Requirement 7: Fail closed on database failure
                raise HTTPException(status_code=503, detail=f"Consent revocation failure: database unavailable ({str(e)})")

            audit_entry = audit_log.append(
                actor_id=actor_id,
                actor_role=actor_role,
                action=f"CONSENT_WITHDRAWN:{scope.value}",
                resource_id=citizen_id,
                details={"scope": scope.value, "previous_granted_at": prev_granted_at}
            )

            updated_record = ConsentRecord(
                id=record_id,
                citizen_id=citizen_id,
                scope=scope,
                granted=False,
                granted_to_helper_id=None,
                granted_at=now,
                revoked_at=now,
                audit_hash=audit_entry.current_hash
            )

            if citizen_id not in self._consents:
                self._consents[citizen_id] = {}
            self._consents[citizen_id][scope] = updated_record

            return updated_record

    def check_consent(
        self,
        citizen_id: str,
        scope: ConsentScope,
        acting_helper_id: Optional[str] = None
    ) -> bool:
        """
        Authoritative check against PostgreSQL storage.
        All API workers observe immediate revocation without stale cache override.
        Fails closed on database error or missing record.
        """
        try:
            from db.connection import SessionLocal
            from db.models import Consent as DBConsent

            with SessionLocal() as db_session:
                db_rec = db_session.query(DBConsent).filter_by(
                    citizen_id=citizen_id,
                    scope=scope.value
                ).first()

                if not db_rec:
                    # Uninitialized scope in DB -> Fail closed (False)
                    with self._lock:
                        if citizen_id in self._consents and scope in self._consents[citizen_id]:
                            del self._consents[citizen_id][scope]
                    return False

                # If revoked in DB, ALWAYS return False and invalidate local cache
                if db_rec.status != ConsentStatus.ACTIVE.value or db_rec.revoked_at is not None:
                    with self._lock:
                        if citizen_id in self._consents and scope in self._consents[citizen_id]:
                            self._consents[citizen_id][scope] = self._consents[citizen_id][scope].model_copy(update={
                                "granted": False,
                                "revoked_at": db_rec.revoked_at
                            })
                    return False

                # If active, verify helper if HELPER_ACTING
                if scope == ConsentScope.HELPER_ACTING and acting_helper_id:
                    return db_rec.grantee == acting_helper_id

                return True

        except Exception:
            # Requirement 7: Fail closed when consent status cannot be verified (e.g. DB connection failure)
            return False

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
            try:
                audit_log.append(
                    actor_id=actor_id,
                    actor_role=actor_role,
                    action=f"UNAUTHORIZED_ACCESS_BLOCKED:{scope.value}",
                    resource_id=citizen_id,
                    details={"scope": scope.value, "reason": "CONSENT_WITHDRAWN_OR_MISSING"}
                )
            except Exception:
                # If audit DB is down during unauthorized access block, still raise ConsentWithdrawnException to fail closed
                pass
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
        """Returns active and revoked consents for a citizen from authoritative PostgreSQL."""
        try:
            from db.connection import SessionLocal
            from db.models import Consent as DBConsent

            with SessionLocal() as db_session:
                records = db_session.query(DBConsent).filter_by(citizen_id=citizen_id).all()
                if records:
                    return {
                        rec.scope: {
                            "granted": (rec.status == ConsentStatus.ACTIVE.value and rec.revoked_at is None),
                            "granted_at": rec.granted_at.isoformat() if rec.granted_at else None,
                            "revoked_at": rec.revoked_at.isoformat() if rec.revoked_at else None,
                            "helper_id": rec.grantee if rec.grantee != "system" else None
                        }
                        for rec in records
                    }
        except Exception:
            pass

        # Fallback to local memory representation if DB query fails
        with self._lock:
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
