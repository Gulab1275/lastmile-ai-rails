"""
Database package for Rahbar.
Managed by Naresh (Supabase Postgres & pgvector).
"""
from .connection import Base, engine, get_db
from .models import (
    AuditLog,
    Case,
    Citizen,
    Consent,
    Decision,
    Delegation,
    Document,
    EvalResult,
    PolicyChunk,
    ReviewItem,
    RuleVersion,
    ScamMessage,
    User,
)

__all__ = [
    "get_db", "engine", "Base",
    "User", "Citizen", "Delegation", "Consent", "Case",
    "Document", "Decision", "RuleVersion", "ReviewItem",
    "AuditLog", "ScamMessage", "EvalResult", "PolicyChunk"
]
