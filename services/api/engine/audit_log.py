"""
Cryptographic Hash-Chained Audit Log.
Implements Hackathon Challenge 05 & Platform Core Requirements.
Every AI, user, and agent action is recorded into an append-only, SHA-256 linked ledger.
Provides verifiable tamper-detection to prove logs have not been manipulated.
"""
import hashlib
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from services.shared.schemas import AuditChainVerificationResponse, AuditLogEntry, RoleEnum

GENESIS_PREV_HASH = "0000000000000000000000000000000000000000000000000000000000000000"


def calculate_hash(
    prev_hash: str,
    timestamp: str,
    actor_id: str,
    actor_role: str,
    action: str,
    resource_id: str,
    details: Dict[str, Any]
) -> str:
    """Calculates SHA-256 hash for an audit ledger block."""
    payload = {
        "prev_hash": prev_hash,
        "timestamp": timestamp,
        "actor_id": actor_id,
        "actor_role": actor_role,
        "action": action,
        "resource_id": resource_id,
        "details": details
    }
    encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class AuditLogLedger:
    def __init__(self):
        self._entries: List[AuditLogEntry] = []
        # Pre-seed with Genesis Event
        self._init_genesis()

    def _init_genesis(self):
        genesis_ts = datetime(2026, 11, 20, 18, 0, 0)
        genesis_hash = calculate_hash(
            prev_hash=GENESIS_PREV_HASH,
            timestamp=genesis_ts.isoformat(),
            actor_id="system",
            actor_role=RoleEnum.ADMIN.value,
            action="GENESIS_SYSTEM_START",
            resource_id="RAHBAR_PLATFORM",
            details={"version": "1.0.0", "event": "Coders Cup '26 DPI Initiation"}
        )
        self._entries.append(
            AuditLogEntry(
                id="audit_genesis_0000",
                prev_hash=GENESIS_PREV_HASH,
                timestamp=genesis_ts,
                actor_id="system",
                actor_role=RoleEnum.ADMIN,
                action="GENESIS_SYSTEM_START",
                resource_id="RAHBAR_PLATFORM",
                details={"version": "1.0.0", "event": "Coders Cup '26 DPI Initiation"},
                current_hash=genesis_hash
            )
        )

    @property
    def latest_hash(self) -> str:
        return self._entries[-1].current_hash if self._entries else GENESIS_PREV_HASH

    def append(
        self,
        actor_id: str,
        actor_role: RoleEnum,
        action: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditLogEntry:
        """
        Appends an immutable entry to the cryptographic hash chain.
        """
        entry_id = f"aud_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow()
        prev = self.latest_hash
        details_dict = details or {}

        current_h = calculate_hash(
            prev_hash=prev,
            timestamp=now.isoformat(),
            actor_id=actor_id,
            actor_role=actor_role.value if isinstance(actor_role, RoleEnum) else str(actor_role),
            action=action,
            resource_id=resource_id,
            details=details_dict
        )

        entry = AuditLogEntry(
            id=entry_id,
            prev_hash=prev,
            timestamp=now,
            actor_id=actor_id,
            actor_role=actor_role,
            action=action,
            resource_id=resource_id,
            details=details_dict,
            current_hash=current_h
        )

        self._entries.append(entry)

        # Dual-persistence to Supabase Postgres
        try:
            from db.connection import SessionLocal
            from db.models import AuditLog as DBAuditLog
            with SessionLocal() as db_session:
                db_entry = DBAuditLog(
                    prev_hash=prev,
                    current_hash=current_h,
                    actor=f"{actor_id}:{actor_role.value if isinstance(actor_role, RoleEnum) else str(actor_role)}",
                    action=action,
                    target=resource_id,
                    result="SUCCESS",
                    request_id=entry_id,
                    timestamp=now
                )
                db_session.add(db_entry)
                db_session.commit()
        except Exception:
            pass

        return entry

    def get_entries(
        self,
        resource_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        limit: int = 100
    ) -> List[AuditLogEntry]:
        """Returns filtered entries sorted from newest to oldest."""
        filtered = self._entries
        if resource_id:
            filtered = [e for e in filtered if e.resource_id == resource_id]
        if actor_id:
            filtered = [e for e in filtered if e.actor_id == actor_id]
        return list(reversed(filtered[-limit:]))

    def verify_chain(self) -> AuditChainVerificationResponse:
        """
        Verifies the cryptographic integrity of the entire audit chain.
        Detects any tampering, deletion, or re-ordering of entries.
        """
        if not self._entries:
            return AuditChainVerificationResponse(
                is_valid=True,
                total_records=0,
                head_hash=None
            )

        expected_prev = GENESIS_PREV_HASH

        for idx, entry in enumerate(self._entries):
            # Check 1: prev_hash linkage
            if entry.prev_hash != expected_prev:
                return AuditChainVerificationResponse(
                    is_valid=False,
                    total_records=len(self._entries),
                    corrupted_at_index=idx,
                    head_hash=self.latest_hash
                )

            # Check 2: recalculate current_hash
            calculated = calculate_hash(
                prev_hash=entry.prev_hash,
                timestamp=entry.timestamp.isoformat(),
                actor_id=entry.actor_id,
                actor_role=entry.actor_role.value if isinstance(entry.actor_role, RoleEnum) else str(entry.actor_role),
                action=entry.action,
                resource_id=entry.resource_id,
                details=entry.details
            )

            if calculated != entry.current_hash:
                return AuditChainVerificationResponse(
                    is_valid=False,
                    total_records=len(self._entries),
                    corrupted_at_index=idx,
                    head_hash=self.latest_hash
                )

            expected_prev = entry.current_hash

        return AuditChainVerificationResponse(
            is_valid=True,
            total_records=len(self._entries),
            corrupted_at_index=None,
            head_hash=self.latest_hash
        )


# Global Singleton Audit Ledger
audit_log = AuditLogLedger()
