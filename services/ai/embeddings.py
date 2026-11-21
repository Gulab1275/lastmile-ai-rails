"""
Semantic Vector Embeddings Engine (Task N9 / Challenge 07: Public Rails).
Generates deterministic, 384-dimensional dense semantic vectors compatible with
pgvector vector(384) in Supabase PostgreSQL.
Provides semantic cosine similarity across Urdu and English policy vocabulary.
"""
import re
import math
import hashlib
from typing import List, Union
import numpy as np

EMBEDDING_DIM = 384

# Key semantic anchor concepts for public relief policy domain
POLICY_ANCHORS = [
    # Eligibility & Demographics
    ("eligibility", "اهلیت", "شرائط", "criteria", "qualify", "requirements"),
    ("widow", "بیوہ", "خاتون", "yateem", "orphan", "single_mother"),
    ("income", "آمدنی", "تنخواہ", "salary", "pkr", "روپے", "poverty", "threshold"),
    ("household", "افراد", "خاندان", "family", "members", "bache", "dependents"),
    ("disability", "معذور", "معذوری", "special_needs", "handicap"),
    
    # Identification & Documents
    ("cnic", "شناختی", "شناختی_کارڈ", "nadra", "identity", "card", "biometric"),
    ("bill", "بجلی", "بل", "utility", "gas", "electricity", "document"),
    ("verification", "تصدیق", "authenticity", "clear", "photo", "blur"),
    
    # Financial & Rails
    ("disbursement", "منظوری", "ادائیگی", "transfer", "payout", "grant", "funds"),
    ("raast", "راست", "state_bank", "account", "iban", "digital_payment"),
    ("limit", "حد", "زیادہ_سے_زیادہ", "maximum", "cap", "ceiling", "threshold"),
    
    # Human Review & Safeguards
    ("officer", "افسر", "جائزہ", "review", "human", "queue", "investigation"),
    ("appeal", "اپیل", "درخواست", "complaint", "shikayat", "grievance"),
    ("no_rejection", "مسترد_نہیں", "zero_auto_reject", "guarantee", "protection"),
    
    # Consent & Data Privacy
    ("consent", "رضامندی", "اختیار", "permission", "authorization", "scope"),
    ("revoke", "منسوخی", "واپس", "withdrawal", "opt_out", "delete", "terminate"),
    ("helper", "مددگار", "کمیونٹی", "community", "delegation", "agent"),
    
    # Fraud & Anti-Scam
    ("scam", "اسکام", "جعلی", "فراڈ", "fake", "fraud", "phishing", "threat"),
    ("otp", "پن", "کوڈ", "pin", "password", "secret", "stolen", "hack"),
    ("official", "سرکاری", "حکومت", "8171", "bisp", "ehsaas", "relief")
]

def _tokenize(text: str) -> List[str]:
    """Tokenizes text preserving both English words and Urdu Unicode tokens."""
    cleaned = re.sub(r"[^\w\s\u0600-\u06FF]", " ", text.lower())
    return [t for t in cleaned.split() if len(t) > 1]

def generate_embedding(text: str, dim: int = EMBEDDING_DIM) -> List[float]:
    """
    Generates a normalized 384-dimensional dense semantic vector for input text.
    Combines semantic anchor projections with n-gram character and word hashing.
    """
    if not text or not text.strip():
        return [0.0] * dim

    tokens = _tokenize(text)
    vec = np.zeros(dim, dtype=np.float32)

    # 1. Semantic anchor projections (first 160 dimensions)
    anchor_span = min(len(POLICY_ANCHORS) * 8, dim // 2)
    for i, anchor_group in enumerate(POLICY_ANCHORS):
        weight = 0.0
        for token in tokens:
            for keyword in anchor_group:
                if keyword in token or token in keyword:
                    weight += 1.5
        if weight > 0.0:
            base_idx = (i * 8) % (dim // 2)
            for offset in range(8):
                idx = base_idx + offset
                # Phase-shifted harmonic encoding
                vec[idx] += weight * math.cos(offset * math.pi / 4.0)

    # 2. Token hash projections with word-level context (middle and upper dimensions)
    for i, token in enumerate(tokens):
        # Word hash
        h_word = int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16)
        pos = h_word % dim
        vec[pos] += 1.0

        # Character trigrams for morphological and root matching
        if len(token) >= 3:
            for j in range(len(token) - 2):
                trigram = token[j:j+3]
                h_tri = int(hashlib.md5(trigram.encode("utf-8")).hexdigest(), 16)
                pos_tri = (h_tri ^ (pos + j)) % dim
                vec[pos_tri] += 0.35

    # 3. L2 Normalization (unit length for exact cosine similarity via dot product)
    norm = np.linalg.norm(vec)
    if norm > 1e-6:
        vec = vec / norm

    return [round(float(x), 6) for x in vec]

def cosine_similarity(vec_a: Union[List[float], np.ndarray], vec_b: Union[List[float], np.ndarray]) -> float:
    """Computes cosine similarity between two dense vectors (-1.0 to 1.0)."""
    a = np.array(vec_a, dtype=np.float32)
    b = np.array(vec_b, dtype=np.float32)
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a < 1e-6 or norm_b < 1e-6:
        return 0.0
    return float(dot / (norm_a * norm_b))
