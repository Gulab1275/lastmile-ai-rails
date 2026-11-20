"""
Database package for Rahbar.
Managed by Naresh (Supabase Postgres & pgvector).
"""
from .connection import get_db, engine, Base
from .models import (
    User, Citizen, Delegation, Consent, Case,
    Document, Decision, RuleVersion, ReviewItem,
    AuditLog, ScamMessage, EvalResult, PolicyChunk
)

__all__ = [
    "get_db", "engine", "Base",
    "User", "Citizen", "Delegation", "Consent", "Case",
    "Document", "Decision", "RuleVersion", "ReviewItem",
    "AuditLog", "ScamMessage", "EvalResult", "PolicyChunk"
]
