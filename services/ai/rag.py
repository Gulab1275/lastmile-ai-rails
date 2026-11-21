"""
Policy Q&A and Supabase pgvector RAG Pipeline (Challenge 07: Public Rails).
Answers citizen and helper questions directly from official relief policy documents with citations.
Powered by Supabase pgvector semantic similarity search and the multi-tier Groq LLM router.
"""
import re
from typing import Dict, Any, List
from sqlalchemy import text
from db.connection import SessionLocal
from db.models import PolicyChunk
from services.ai.router import route_llm
from services.ai.embeddings import generate_embedding, cosine_similarity

# In-memory baseline policies for offline resilience
MOCK_POLICIES = [
    {
        "document_name": "National Relief Cash Support Guidelines 2026",
        "page_number": 2,
        "content": (
            "Section 2.1: Eligibility Criteria. "
            "Assistance is provided to households with a verified monthly income below PKR 35,000. "
            "Widows, persons with disabilities, and daily wage earners receive priority scoring. "
            "A valid 13-digit CNIC is mandatory for identity verification."
        )
    },
    {
        "document_name": "National Relief Cash Support Guidelines 2026",
        "page_number": 4,
        "content": (
            "Section 4.1: Cash Payout Rails and Raast Instant Settlement. "
            "Approved cash relief grants of PKR 12,000 are disbursed instantaneously via the State Bank of Pakistan's "
            "Raast P2P rails and 1Link network. Payouts require a cryptographic HMAC approval token."
        )
    },
    {
        "document_name": "National Relief Cash Support Guidelines 2026",
        "page_number": 5,
        "content": (
            "Section 4.3: Disbursement Limits and Anti-Fraud Measures. "
            "The maximum single disbursement is capped at PKR 25,000. "
            "Any claim exceeding this threshold requires mandatory two-tier human officer review. "
            "No processing fee, OTP, or advance deposit is ever requested by official relief personnel."
        )
    },
    {
        "document_name": "Community Helper & 40-Family Protection Code 2026",
        "page_number": 2,
        "content": (
            "Section 2.4: Granular Consent Gateway and Right to Revoke. "
            "Citizens retain full ownership over their shared personal and financial records. "
            "A citizen or authorized helper may withdraw data-sharing consent at any time. "
            "Upon withdrawal, access to the citizen's profile is immediately terminated across all systems."
        )
    },
    {
        "document_name": "قومی امدادی کیش پروگرام برائے کمزور طبقات 2026",
        "page_number": 1,
        "content": (
            "باب اول: اہلیت، آمدنی کی حد اور بیوہ خواتین کا وظیفہ۔ "
            "قومی ریلیف پروگرام کے تحت صرف وہ خاندان اہل ہیں جن کی تصدیق شدہ ماہانہ آمدنی 35,000 روپے سے کم ہو۔ "
            "بیوہ خواتین، یتیم بچوں، اور معذور افراد کو امداد کی فراہمی میں ترجیحی اسکور دیا جائے گا۔ "
            "نادرا کا 13 ہندسوں پر مشتمل شناختی کارڈ شناختی تصدیق کے لیے لازمی ہے۔"
        )
    }
]

def search_policy_chunks(query: str, limit: int = 3) -> List[Dict[str, Any]]:
    """
    Retrieves matching policy chunks from Supabase pgvector semantic search.
    Gracefully falls back to in-memory cosine similarity and keyword matching if offline.
    """
    query_vector = generate_embedding(query)
    q_emb_str = "[" + ",".join(str(x) for x in query_vector) + "]"

    session = SessionLocal()
    results = []
    
    # 1. Primary: Native Supabase pgvector Cosine Distance Query
    try:
        sql = text("""
            SELECT 
                id, 
                document_name, 
                page_number, 
                content, 
                1 - (embedding <=> CAST(:q_emb AS vector)) AS similarity
            FROM policy_chunks
            ORDER BY embedding <=> CAST(:q_emb AS vector) ASC
            LIMIT :limit;
        """)
        rows = session.execute(sql, {"q_emb": q_emb_str, "limit": limit}).fetchall()
        for r in rows:
            results.append({
                "document_name": r[1],
                "page_number": r[2],
                "excerpt": r[3],
                "similarity": round(float(r[4]), 4) if r[4] is not None else 0.50,
                "retrieval_mode": "supabase_pgvector"
            })
    except Exception as e:
        # Fallback to ORM chunks query with in-memory vector comparison
        try:
            chunks = session.query(PolicyChunk).all()
            if chunks:
                scored = []
                for c in chunks:
                    sim = 0.0
                    if c.embedding_json:
                        sim = cosine_similarity(query_vector, c.embedding_json)
                    scored.append((sim, c))
                scored.sort(key=lambda x: x[0], reverse=True)
                for sim, item in scored[:limit]:
                    results.append({
                        "document_name": item.document_name,
                        "page_number": item.page_number,
                        "excerpt": item.content,
                        "similarity": round(sim, 4),
                        "retrieval_mode": "orm_vector_fallback"
                    })
        except Exception:
            pass
    finally:
        session.close()

    # 2. Resilient Offline Fallback (MOCK_POLICIES)
    if not results:
        scored = []
        for p in MOCK_POLICIES:
            p_emb = generate_embedding(p["content"])
            sim = cosine_similarity(query_vector, p_emb)
            scored.append((sim, p))
        scored.sort(key=lambda x: x[0], reverse=True)
        results = [
            {
                "document_name": x[1]["document_name"],
                "page_number": x[1]["page_number"],
                "excerpt": x[1]["content"],
                "similarity": round(x[0], 4),
                "retrieval_mode": "local_resilient_fallback"
            }
            for x in scored[:limit]
        ]

    return results

def ask_policy(question: str) -> Dict[str, Any]:
    """
    RAG endpoint answering citizen queries based on policy documents.
    Supports both Urdu and English questions with exact page and document citations.
    """
    if not question or not question.strip():
        return {
            "answer": "Please provide a question regarding the relief cash support program.",
            "sources": [],
            "retrieval_mode": "none"
        }

    sources = search_policy_chunks(question, limit=3)
    retrieval_mode = sources[0].get("retrieval_mode", "supabase_pgvector") if sources else "none"

    context_text = "\n\n".join([
        f"Source: {s['document_name']} (Page {s['page_number']})\n{s.get('excerpt', s.get('content', ''))}"
        for s in sources
    ])

    messages = [
        {
            "role": "system",
            "content": (
                "You are Rahbar (رہبر), the official AI policy assistant for the National Public Relief & Social Protection Rails. "
                "Answer the citizen's or helper's question clearly, accurately, and empathetically based ONLY on the provided policy context. "
                "Rules:\n"
                "1. If the question is in Urdu, respond in natural, polite Urdu (اردو). If in English, respond in English.\n"
                "2. ALWAYS cite the exact Document Name and Page Number for every claim.\n"
                "3. If the answer is not mentioned in the policy context, state clearly that official guidelines do not specify it.\n"
                "4. Be concise and accessible to low-literacy citizens."
            )
        },
        {
            "role": "user",
            "content": f"Official Policy Context:\n{context_text}\n\nUser Question:\n{question}"
        }
    ]

    llm_res = route_llm(messages, temperature=0.1)

    clean_sources = []
    for s in sources:
        clean_sources.append({
            "document_name": s["document_name"],
            "page_number": s["page_number"],
            "excerpt": s.get("excerpt", s.get("content", ""))[:250],
            "similarity": s.get("similarity", 0.85)
        })

    return {
        "answer": llm_res.get("content", "").strip(),
        "sources": clean_sources,
        "provider": llm_res.get("provider", "groq"),
        "retrieval_mode": retrieval_mode
    }
