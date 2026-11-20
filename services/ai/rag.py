"""
Policy Q&A and RAG Pipeline.
Answers citizen and helper questions directly from official relief policy documents with citations.
Integrates Supabase Postgres (policy_chunks) and the multi-tier LLM router.
"""
from typing import Dict, Any, List
from sqlalchemy import text
from db.connection import SessionLocal
from db.models import PolicyChunk
from services.ai.router import route_llm

MOCK_POLICIES = [
    {
        "document_name": "National Relief Cash Support Guidelines 2026",
        "page_number": 2,
        "content": (
            "Section 2.1: Eligibility Criteria. "
            "Assistance is provided to households with a verified monthly income below PKR 45,000. "
            "Widows, persons with disabilities, and daily wage earners receive priority scoring. "
            "A valid 13-digit CNIC is mandatory for identity verification."
        )
    },
    {
        "document_name": "National Relief Cash Support Guidelines 2026",
        "page_number": 4,
        "content": (
            "Section 4.3: Disbursement Limits and Anti-Fraud Measures. "
            "The maximum single disbursement is capped at PKR 25,000. "
            "Any claim exceeding this threshold requires mandatory two-tier human officer review. "
            "No processing fee, OTP, or advance deposit is ever requested by official relief personnel."
        )
    },
    {
        "document_name": "Citizen Data Protection and Consent Protocol",
        "page_number": 1,
        "content": (
            "Section 1.2: Right to Revoke. "
            "Citizens retain full ownership over their shared personal and financial records. "
            "A citizen or authorized helper may withdraw data-sharing consent at any time. "
            "Upon withdrawal, access to the citizen's profile is immediately terminated across all systems."
        )
    }
]

def search_policy_chunks(query: str, limit: int = 3) -> List[Dict[str, Any]]:
    """
    Retrieves matching policy chunks from Supabase or memory.
    """
    session = SessionLocal()
    results = []
    try:
        # Check DB first
        chunks = session.query(PolicyChunk).all()
        if chunks:
            # Simple keyword matching over chunks
            scored = []
            q_words = set(query.lower().split())
            for c in chunks:
                c_words = set(c.content.lower().split())
                score = len(q_words.intersection(c_words))
                scored.append((score, c))
            scored.sort(key=lambda x: x[0], reverse=True)
            for _, item in scored[:limit]:
                results.append({
                    "document_name": item.document_name,
                    "page_number": item.page_number,
                    "excerpt": item.content
                })
    except Exception as e:
        print(f"DB search warning: {e}")
    finally:
        session.close()

    # Fallback to embedded policies if DB empty
    if not results:
        q_words = set(query.lower().split())
        scored = []
        for p in MOCK_POLICIES:
            p_words = set(p["content"].lower().split())
            score = len(q_words.intersection(p_words))
            scored.append((score, p))
        scored.sort(key=lambda x: x[0], reverse=True)
        results = [x[1] for x in scored[:limit]]

    return results

def ask_policy(question: str) -> Dict[str, Any]:
    """
    RAG endpoint answering citizen queries based on policy documents.
    """
    if not question or not question.strip():
        return {
            "answer": "Please provide a question regarding the relief cash support program.",
            "sources": []
        }

    sources = search_policy_chunks(question, limit=2)
    context_text = "\n\n".join([
        f"Source: {s['document_name']} (Page {s['page_number']})\n{s['content'] if 'content' in s else s['excerpt']}"
        for s in sources
    ])

    messages = [
        {
            "role": "system",
            "content": (
                "You are Rahbar, an official public relief policy assistant. "
                "Answer the user's question clearly, concisely, and accurately based ONLY on the provided policy context. "
                "Always cite the document name and page number. If the answer is not in the context, state that clearly."
            )
        },
        {
            "role": "user",
            "content": f"Policy Context:\n{context_text}\n\nUser Question:\n{question}"
        }
    ]

    llm_res = route_llm(messages, temperature=0.1)
    
    clean_sources = []
    for s in sources:
        clean_sources.append({
            "document_name": s["document_name"],
            "page_number": s["page_number"],
            "excerpt": s.get("excerpt", s.get("content", ""))[:200]
        })

    return {
        "answer": llm_res["content"],
        "sources": clean_sources,
        "provider": llm_res.get("provider")
    }
