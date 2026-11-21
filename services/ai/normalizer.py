"""
Roman Urdu Phonetic Soundex & Dialect Normalizer.
Normalizes colloquial Pakistani SMS, WhatsApp, and social media text
to handle phonetic variations, slang, and intentional evasion.
"""

import re

# Phonetic and colloquial mappings for Pakistani SMS / WhatsApp communication
PHONETIC_REPLACEMENTS = [
    # Repeated characters (e.g., 'soooch' -> 'soch', 'feeees' -> 'fees')
    (r"([a-zA-Z])\1{2,}", r"\1\1"),

    # Financial / payment terms
    (r"\b(paisa|paisay|pesay|pese|paise|pesa)\b", "rupaye"),
    (r"\b(rupy|rupiye|rupaiye|rupees|rs\.?|pkr)\b", "rupaye"),
    (r"\b(feez|fess|chargis|taxx|tex)\b", "fee"),
    (r"\b(advans|adwance|adwans)\b", "advance"),
    (r"\b(easypaisa|easy_paisa|jazzcash|jazz_cash)\b", "easypaisa"),

    # Urgency & Call to action
    (r"\b(fawran|forun|forn|fooran|jldi|jaldi|urgnt|urgent)\b", "foran"),
    (r"\b(bhejo|bhejein|bhejain|bhejna|snd|sand)\b", "bhejo"),
    (r"\b(kren|krain|karein|kro|karo)\b", "karein"),
    (r"\b(milega|milyga|miley ga|milenge|mily gy)\b", "milega"),
    (r"\b(raabta|rabta|contact|call)\b", "rabta"),

    # Social protection & government programs
    (r"\b(ehsas|ehasas|ihsas|ihsaas)\b", "ehsaas"),
    (r"\b(benazir|benezir|bisp)\b", "benazir"),
    (r"\b(wazifa|wazeefa|wazeepha|wazifah)\b", "wazifa"),
    (r"\b(hukumat|hakomat|gov|govt)\b", "hukumat"),
    (r"\b(sarif|sareef|costumer|customer)\b", "sarif"),
    (r"\b(mubarak|mubarik|mobarak|mbrk)\b", "mubarak"),

    # Authentication & credentials
    (r"\b(passwrd|pswd|pin_code|pincode)\b", "pin"),
    (r"\b(shanakhti|shanakht|cnic_no)\b", "cnic"),
    (r"\b(acnt|acc|accont)\b", "account"),
    (r"\b(shukria|shukriya|thnx|thanks)\b", "shukriya")
]

def normalize_roman_urdu(text: str) -> str:
    """
    Normalizes Roman Urdu text into standardized phonetic tokens.
    Handles space anomalies in phone numbers and URLs.
    """
    if not text or not text.strip():
        return ""

    normalized = text.lower().strip()

    # Normalize phone numbers with spaces e.g. "0300 123 4567" -> "03001234567"
    normalized = re.sub(r"\b(03\d{2})\s+(\d{3})\s+(\d{4})\b", r"\1\2\3", normalized)
    normalized = re.sub(r"\b(03\d{2})\s+(\d{7})\b", r"\1\2", normalized)

    # Apply phonetic rules
    for pattern, replacement in PHONETIC_REPLACEMENTS:
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)

    # Flatten excessive whitespace
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized
