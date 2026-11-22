-- ==============================================================================
-- Migration 003: Database-Level Append-Only Trigger for audit_log Table
-- Target: Supabase PostgreSQL (Post-Remediation Security Control)
-- Prevents UPDATE and DELETE operations by any database role, ensuring ledger immutability
-- ==============================================================================

-- 1. Create tamper prevention trigger function
CREATE OR REPLACE FUNCTION prevent_audit_log_tamper()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'TAMPER_PREVENTION: The audit_log table is strictly append-only. Modification (UPDATE), deletion (DELETE), or truncation (TRUNCATE) of audit records is prohibited by security policy.'
        USING ERRCODE = '55000'; -- object_not_in_prerequisite_state
END;
$$ LANGUAGE plpgsql;

-- 2. Drop existing triggers if already present
DROP TRIGGER IF EXISTS trg_audit_log_append_only ON audit_log;
DROP TRIGGER IF EXISTS trg_audit_log_truncate ON audit_log;

-- 3. Create BEFORE UPDATE OR DELETE row-level trigger
CREATE TRIGGER trg_audit_log_append_only
BEFORE UPDATE OR DELETE ON audit_log
FOR EACH ROW
EXECUTE FUNCTION prevent_audit_log_tamper();

-- 4. Create BEFORE TRUNCATE statement-level trigger
CREATE TRIGGER trg_audit_log_truncate
BEFORE TRUNCATE ON audit_log
FOR EACH STATEMENT
EXECUTE FUNCTION prevent_audit_log_tamper();

-- Verification Query:
-- SELECT trigger_name, event_manipulation, event_object_table, action_statement
-- FROM information_schema.triggers
-- WHERE event_object_table = 'audit_log';
