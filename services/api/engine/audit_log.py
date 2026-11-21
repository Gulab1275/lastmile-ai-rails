"""
Cryptographic Hash-Chained Audit Log.
Implements Hackathon Challenge 05 & Platform Core Requirements.
Authoritative Source: PostgreSQL database table 'audit_log'.
Every AI, user, and agent action is recorded into an append-only, SHA-256 linked ledger.
Provides verifiable tamper-detection across all distributed worker processes.
"""
import hashlib
import hmac
import json
import os
import threading
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import text

from services.shared.schemas import AuditChainVerificationResponse, AuditLogEntry, RoleEnum

GENESIS_PREV_HASH = "0000000000000000000000000000000000000000000000000000000000000000"
AUDIT_LOCK_ID = 991288  # PostgreSQL transaction advisory lock for serializing appends


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
        self._lock = threading.Lock()
        self._entries: List[AuditLogEntry] = []
        self._sync_from_db()

    def _sync_from_db(self):
        """Loads entries from PostgreSQL authoritative store, or initializes genesis if empty."""
        genesis_ts = datetime(2026, 11, 20, 18, 0, 0)
        genesis_details = {"version": "1.0.0", "event": "Coders Cup '26 DPI Initiation"}
        genesis_hash = calculate_hash(
            prev_hash=GENESIS_PREV_HASH,
            timestamp=genesis_ts.isoformat(),
            actor_id="system",
            actor_role=RoleEnum.ADMIN.value,
            action="GENESIS_SYSTEM_START",
            resource_id="RAHBAR_PLATFORM",
            details=genesis_details
        )
        genesis_entry = AuditLogEntry(
            id="audit_genesis_0000",
            prev_hash=GENESIS_PREV_HASH,
            timestamp=genesis_ts,
            actor_id="system",
            actor_role=RoleEnum.ADMIN,
            action="GENESIS_SYSTEM_START",
            resource_id="RAHBAR_PLATFORM",
            details=genesis_details,
            current_hash=genesis_hash
        )

        try:
            from db.connection import SessionLocal
            from db.models import AuditLog as DBAuditLog
            with SessionLocal() as db_session:
                rows = db_session.query(DBAuditLog).order_by(DBAuditLog.id.asc()).all()
                if not rows:
                    # Insert Genesis block into PostgreSQL
                    db_entry = DBAuditLog(
                        prev_hash=GENESIS_PREV_HASH,
                        current_hash=genesis_hash,
                        actor=f"system:{RoleEnum.ADMIN.value}",
                        action="GENESIS_SYSTEM_START",
                        target="RAHBAR_PLATFORM",
                        result="SUCCESS",
                        request_id="audit_genesis_0000",
                        timestamp=genesis_ts,
                        details=genesis_details
                    )
                    db_session.add(db_entry)
                    db_session.commit()
                    self._entries = [genesis_entry]
                else:
                    loaded = []
                    for r in rows:
                        parts = r.actor.split(":", 1)
                        role_str = parts[1] if len(parts) > 1 else "system"
                        try:
                            role = RoleEnum(role_str)
                        except Exception:
                            role = RoleEnum.ADMIN
                        loaded.append(AuditLogEntry(
                            id=r.request_id or f"aud_{r.id}",
                            prev_hash=r.prev_hash,
                            timestamp=r.timestamp,
                            actor_id=parts[0],
                            actor_role=role,
                            action=r.action,
                            resource_id=r.target,
                            details=r.details or {},
                            current_hash=r.current_hash
                        ))
                    self._entries = loaded
        except Exception:
            # Fallback to local genesis if database is unreachable during init
            self._entries = [genesis_entry]

    @property
    def latest_hash(self) -> str:
        try:
            from db.connection import SessionLocal
            from db.models import AuditLog as DBAuditLog
            with SessionLocal() as db_session:
                latest = db_session.query(DBAuditLog).order_by(DBAuditLog.id.desc()).first()
                if latest:
                    return latest.current_hash
        except Exception:
            pass
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
        Authoritative write to PostgreSQL with distributed advisory lock.
        Fails closed on database outage to ensure zero silent audit loss.
        """
        entry_id = f"aud_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow()
        details_dict = details or {}
        actor_role_str = actor_role.value if isinstance(actor_role, RoleEnum) else str(actor_role)

        from db.connection import SessionLocal
        from db.models import AuditLog as DBAuditLog

        try:
            with SessionLocal() as db_session:
                # Advisory transaction lock guarantees strict sequential serialization across worker processes
                if db_session.bind and db_session.bind.dialect.name == "postgresql":
                    db_session.execute(text(f"SELECT pg_advisory_xact_lock({AUDIT_LOCK_ID});"))

                latest_db = db_session.query(DBAuditLog).order_by(DBAuditLog.id.desc()).first()
                prev = latest_db.current_hash if latest_db else GENESIS_PREV_HASH

                current_h = calculate_hash(
                    prev_hash=prev,
                    timestamp=now.isoformat(),
                    actor_id=actor_id,
                    actor_role=actor_role_str,
                    action=action,
                    resource_id=resource_id,
                    details=details_dict
                )

                db_entry = DBAuditLog(
                    prev_hash=prev,
                    current_hash=current_h,
                    actor=f"{actor_id}:{actor_role_str}",
                    action=action,
                    target=resource_id,
                    result="SUCCESS",
                    request_id=entry_id,
                    timestamp=now,
                    details=details_dict
                )
                db_session.add(db_entry)
                db_session.commit()
        except Exception as e:
            # Task 2 requirement: Database outage does not silently lose required audit events
            raise RuntimeError(f"Audit log persistence failure: database unavailable ({str(e)})")

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
        with self._lock:
            if self._entries and self._entries[-1].current_hash != prev:
                self._sync_from_db()
            else:
                self._entries.append(entry)
        return entry

    def get_entries(
        self,
        resource_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        limit: int = 100
    ) -> List[AuditLogEntry]:
        """Returns filtered entries from authoritative PostgreSQL store (with fallback to local)."""
        from db.connection import SessionLocal
        from db.models import AuditLog as DBAuditLog
        try:
            with SessionLocal() as db_session:
                q = db_session.query(DBAuditLog)
                if resource_id:
                    q = q.filter(DBAuditLog.target == resource_id)
                if actor_id:
                    q = q.filter(DBAuditLog.actor.like(f"{actor_id}:%"))
                db_rows = q.order_by(DBAuditLog.id.desc()).limit(limit).all()
                if db_rows:
                    result = []
                    for r in db_rows:
                        parts = r.actor.split(":", 1)
                        role_str = parts[1] if len(parts) > 1 else "system"
                        try:
                            role = RoleEnum(role_str)
                        except Exception:
                            role = RoleEnum.ADMIN
                        result.append(AuditLogEntry(
                            id=r.request_id or f"aud_{r.id}",
                            prev_hash=r.prev_hash,
                            timestamp=r.timestamp,
                            actor_id=parts[0],
                            actor_role=role,
                            action=r.action,
                            resource_id=r.target,
                            details=r.details or {},
                            current_hash=r.current_hash
                        ))
                    return result
        except Exception:
            pass

        filtered = self._entries
        if resource_id:
            filtered = [e for e in filtered if e.resource_id == resource_id]
        if actor_id:
            filtered = [e for e in filtered if e.actor_id == actor_id]
        return list(reversed(filtered[-limit:]))

    def verify_chain(self, from_db: bool = True) -> AuditChainVerificationResponse:
        """
        Verifies the cryptographic integrity of the entire audit chain.
        Detects any tampering, deletion, or re-ordering of entries.
        Authoritative source is PostgreSQL.
        """
        # First check in-memory entries (catches memory tampering and unit test mocks)
        if self._entries:
            exp_prev = GENESIS_PREV_HASH
            for idx, entry in enumerate(self._entries):
                if entry.prev_hash != exp_prev:
                    return AuditChainVerificationResponse(
                        is_valid=False,
                        total_records=len(self._entries),
                        corrupted_at_index=idx,
                        head_hash=self._entries[-1].current_hash,
                    )
                actor_role_str = entry.actor_role.value if isinstance(entry.actor_role, RoleEnum) else str(entry.actor_role)
                calculated = calculate_hash(
                    prev_hash=entry.prev_hash,
                    timestamp=entry.timestamp.isoformat() if hasattr(entry.timestamp, "isoformat") else str(entry.timestamp),
                    actor_id=entry.actor_id,
                    actor_role=actor_role_str,
                    action=entry.action,
                    resource_id=entry.resource_id,
                    details=entry.details or {},
                )
                if calculated != entry.current_hash:
                    return AuditChainVerificationResponse(
                        is_valid=False,
                        total_records=len(self._entries),
                        corrupted_at_index=idx,
                        head_hash=self._entries[-1].current_hash,
                    )
                exp_prev = entry.current_hash

        # If from_db is True, perform authoritative verification against PostgreSQL
        if from_db:
            from db.connection import SessionLocal
            from db.models import AuditLog as DBAuditLog

            try:
                with SessionLocal() as db_session:
                    db_entries = db_session.query(DBAuditLog).order_by(DBAuditLog.id.asc()).all()
                    if not db_entries:
                        return AuditChainVerificationResponse(
                            is_valid=True,
                            total_records=0,
                            head_hash=GENESIS_PREV_HASH
                        )

                    expected_prev = GENESIS_PREV_HASH
                    head_hash = db_entries[-1].current_hash

                    for idx, entry in enumerate(db_entries):
                        # Check 1: prev_hash linkage
                        if entry.prev_hash != expected_prev:
                            return AuditChainVerificationResponse(
                                is_valid=False,
                                total_records=len(db_entries),
                                corrupted_at_index=idx,
                                head_hash=head_hash
                            )

                        # Check 2: recalculate current_hash
                        actor_parts = entry.actor.split(":", 1)
                        actor_id = actor_parts[0]
                        actor_role = actor_parts[1] if len(actor_parts) > 1 else "system"

                        calculated = calculate_hash(
                            prev_hash=entry.prev_hash,
                            timestamp=entry.timestamp.isoformat(),
                            actor_id=actor_id,
                            actor_role=actor_role,
                            action=entry.action,
                            resource_id=entry.target,
                            details=entry.details or {}
                        )

                        if calculated != entry.current_hash:
                            return AuditChainVerificationResponse(
                                is_valid=False,
                                total_records=len(db_entries),
                                corrupted_at_index=idx,
                                head_hash=head_hash
                            )

                        expected_prev = entry.current_hash

                    return AuditChainVerificationResponse(
                        is_valid=True,
                        total_records=len(db_entries),
                        corrupted_at_index=None,
                        head_hash=head_hash
                    )
            except Exception:
                # Fallback to local memory verification if DB connection drops
                pass

        # In-memory mirror verification (when from_db=False or during unit test mocks)
        if not self._entries:
            return AuditChainVerificationResponse(
                is_valid=True,
                total_records=0,
                head_hash=GENESIS_PREV_HASH
            )

        exp_prev = GENESIS_PREV_HASH
        for idx, entry in enumerate(self._entries):
            if entry.prev_hash != exp_prev:
                return AuditChainVerificationResponse(
                    is_valid=False,
                    total_records=len(self._entries),
                    corrupted_at_index=idx,
                    head_hash=self._entries[-1].current_hash
                )
            actor_role_str = entry.actor_role.value if isinstance(entry.actor_role, RoleEnum) else str(entry.actor_role)
            calculated = calculate_hash(
                prev_hash=entry.prev_hash,
                timestamp=entry.timestamp.isoformat(),
                actor_id=entry.actor_id,
                actor_role=actor_role_str,
                action=entry.action,
                resource_id=entry.resource_id,
                details=entry.details
            )
            if calculated != entry.current_hash:
                return AuditChainVerificationResponse(
                    is_valid=False,
                    total_records=len(self._entries),
                    corrupted_at_index=idx,
                    head_hash=self._entries[-1].current_hash
                )
            exp_prev = entry.current_hash

        return AuditChainVerificationResponse(
            is_valid=True,
            total_records=len(self._entries),
            corrupted_at_index=None,
            head_hash=self._entries[-1].current_hash
        )

    def create_signed_checkpoint(
        self,
        secret_key: Optional[str] = None,
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Creates an independently protected, cryptographically signed audit checkpoint.
        Anchors the current ledger height and head_hash outside the primary database.
        Detects database truncation (deleting the newest record) and historical hash recalculation.
        Fails closed when AUDIT_CHECKPOINT_KEY is missing (hardcoded fallbacks prohibited).
        """
        key_str = secret_key or os.getenv("AUDIT_CHECKPOINT_KEY")
        if not key_str:
            raise ValueError(
                "AUDIT_CHECKPOINT_KEY is missing. Hardcoded key fallback is strictly prohibited. "
                "A cryptographically secure signing key must be injected via external environment or KMS."
            )
        key = key_str.encode("utf-8")

        # Verify current chain first
        chain_status = self.verify_chain(from_db=True)
        if not chain_status.is_valid:
            raise RuntimeError(f"Cannot create checkpoint: audit chain is invalid at index {chain_status.corrupted_at_index}")

        height = chain_status.total_records
        head_h = chain_status.head_hash
        now_ts = datetime.utcnow().isoformat()
        checkpoint_id = f"chk_{uuid.uuid4().hex[:12]}"

        # Sign the checkpoint: HMAC-SHA256(key, id || height || head_hash || timestamp)
        msg = f"{checkpoint_id}:{height}:{head_h}:{now_ts}".encode("utf-8")
        signature = hmac.new(key, msg, hashlib.sha256).hexdigest()

        checkpoint = {
            "checkpoint_id": checkpoint_id,
            "height": height,
            "head_hash": head_h,
            "timestamp": now_ts,
            "signature": signature,
            "algorithm": "HMAC-SHA256"
        }

        if output_file:
            try:
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(checkpoint, f, indent=2)
            except Exception:
                pass

        return checkpoint

    def verify_checkpoint(
        self,
        checkpoint: Dict[str, Any],
        secret_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verifies a signed checkpoint and checks the database audit ledger against it.
        Detects:
        - Deleting the newest audit record (database height < checkpoint height)
        - Deleting intermediate records (broken hash linkage)
        - Modifying records (hash mismatch)
        - Modifying historical records and recalculating subsequent hashes (head_hash != checkpoint head_hash)
        Fails closed when AUDIT_CHECKPOINT_KEY is missing.
        """
        key_str = secret_key or os.getenv("AUDIT_CHECKPOINT_KEY")
        if not key_str:
            raise ValueError(
                "AUDIT_CHECKPOINT_KEY is missing. Cannot verify checkpoint signature without signing key."
            )
        key = key_str.encode("utf-8")

        # 1. Verify signature of the checkpoint itself
        msg = f"{checkpoint['checkpoint_id']}:{checkpoint['height']}:{checkpoint['head_hash']}:{checkpoint['timestamp']}".encode("utf-8")
        expected_sig = hmac.new(key, msg, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected_sig, checkpoint.get("signature", "")):
            return {
                "is_valid": False,
                "reason": "CHECKPOINT_SIGNATURE_INVALID",
                "detail": "Checkpoint signature is forged or corrupted."
            }

        # 2. Verify DB chain from Genesis
        chain_status = self.verify_chain(from_db=True)
        if not chain_status.is_valid:
            return {
                "is_valid": False,
                "reason": "INTERNAL_CHAIN_BROKEN",
                "detail": f"Internal hash chain broken at index {chain_status.corrupted_at_index}."
            }

        # 3. Check for Truncation (e.g. newest record deleted)
        if chain_status.total_records < checkpoint["height"]:
            return {
                "is_valid": False,
                "reason": "LEDGER_TRUNCATION_DETECTED",
                "detail": f"Database has {chain_status.total_records} records but checkpoint requires {checkpoint['height']}. Newest record(s) were deleted!"
            }

        # 4. Check for Head Hash divergence (e.g. historical recalculation attack)
        from db.connection import SessionLocal
        from db.models import AuditLog as DBAuditLog
        with SessionLocal() as db_session:
            chk_row = db_session.query(DBAuditLog).order_by(DBAuditLog.id.asc()).offset(checkpoint["height"] - 1).first()
            if not chk_row or chk_row.current_hash != checkpoint["head_hash"]:
                return {
                    "is_valid": False,
                    "reason": "HEAD_HASH_MISMATCH_HISTORICAL_RECALCULATION",
                    "detail": "Database head hash at checkpoint height does not match signed checkpoint. Historical records were rewritten!"
                }

        return {
            "is_valid": True,
            "checkpoint_height": checkpoint["height"],
            "current_height": chain_status.total_records,
            "head_hash_verified": True
        }


# Global Singleton Audit Ledger
audit_log = AuditLogLedger()
