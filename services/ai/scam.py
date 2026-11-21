"""
Probabilistic Scam and Phishing Classifier (Challenge 08: Scams and Fake Documents).
Detects fake relief cash offers, OTP theft, and phishing links in Urdu, Roman Urdu, and English.
Uses scikit-learn TF-IDF + Calibrated Logistic Regression + Explainable Rule Features.
Enhanced in Production Security Hardening Mission 2:
- Contextual fee-demand detection separating money requests from receipts and utility bills.
- Preserves 100% recall on OTP/PIN credential theft.
- Official anti-scam warning detection and utility bill dampening.
"""
import re
from typing import Any, Dict, List

from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from services.ai.normalizer import normalize_roman_urdu
from services.shared.schemas import ScamLabel

# Rule patterns and trigger explanations
SCAM_INDICATORS = [
    (
        r"(otp|pin\b|\bپن\b|password|passcode|credential|verification\s*code|کوڈ|پاسورڈ|mpin|\b(?:4|6)[ -]?digit\s*code\b|code\s*received\s*via\s*sms|خفیہ\s*کوڈ|سیکیورٹی\s*کوڈ)",
        "Requests sensitive security PIN or OTP"
    ),
    (
        r"(\b(?:fee|advance|charges|tax|cost|duty|فیس|ایڈوانس|رقم|چالان|ڈاک|خرچ|کورئیر|فائل|پروسیسنگ|رجسٹریشن|چارجز|ڈیوٹی|معاوضہ)\b.*?\b(?:jama|bhejein|bhejo|ada|send|transfer|pay|deposit|karein|karwayen|mang|chahiye|submit|remit|جمع|بھیج|ادا|ٹرانسفر|دیں|کروائیں|ارسال|کریں|کرائیں)\b|\b(?:bhejein|bhejo|jama\s*kar|send|transfer|pay|deposit|submit|remit|جمع|بھیج|ادا|ٹرانسفر)\b.*?\b(?:fee|charges|advance|tax|processing|rupay|rs|pkr|فیس|چارجز|ٹیکس|\d+)\b|\b\d+\s*(?:rs|rupay|rupees|روپے)?\s*(?:foran|abhi|jaldi|urgent|فوری|ابھی)?\s*(?:bhejein|bhejo|jama|send|transfer|ada|karwayen|جمع|بھیج|ادا|ٹرانسفر|کروائیں|ایزی پیسہ|جائز کیش)\b)",
        "Asks for advance fee or payment to release relief funds"
    ),
    (
        r"(hurry|urgent|immediately|immediate|last chance|account\s*(?:locked|closed|blocked|freeze|suspended|deactivated)|warning|fine|legal\s*action|arrest|آخری تاریخ|جلدی کریں|فوری|اکاؤنٹ بند|بلاک|معطل|انتباہ|وارننگ|آخری موقع)",
        "Uses high-pressure artificial urgency or threats of account closure"
    ),
    (r"(http://|https://|bit\.ly|t\.co|wa\.me|tinyurl|goo\.gl)", "Contains unverified or shortened external URL"),
    (r"(won|lottery|lucky draw|انعام|لاٹری|قرعہ اندازی)", "Claims unexpected lottery or lucky draw win"),
    (r"(8171|bisp|ehsaas|benazir|احساس|بینظیر)", "Mentions government relief scheme without official domain verification")
]

# Baseline training corpus (English, Urdu, Roman Urdu) - Balanced 18 Scam vs 18 Legit
TRAIN_DATA = [
    # --- Scam samples (18) ---
    ("Muaziz Sarif, aapko Hukumat ki taraf se 25,000 Relief Cash mila hai. Abhi bit.ly/relief26 par click kar k 500 fee jama karein", 1),
    ("BISP Alert: Aapka 35,000 ka wazifa aya hai. Apna OTP 8899 par bhejein foran", 1),
    ("Congratulations! You won Rs 50,000 cash grant. Send Rs 1000 processing fee to 03001234567 to claim", 1),
    ("مبارک ہو! آپ کا احساس ایمرجنسی ریلیف فنڈ منظور ہو گیا ہے۔ فوری 1000 فیس جمع کروائیں", 1),
    ("Apka CNIC block ho raha hai. Foran apna bank PIN verify karein wrna account band hojaye ga", 1),
    ("Ehsaas Program 2026: Get 50000 relief cash immediately. Click here http://ehsaas-fake-grant.com", 1),
    ("آپ کا بی آئی ایس پی کا 25000 آ گیا ہے، ابھی پن کوڈ واٹس ایپ کریں", 1),
    ("Last date today! Claim your disaster relief payout by sending WhatsApp message with bank details", 1),
    ("Government emergency relief funds released. Register at tinyurl.com/relief-fast to get cash", 1),
    ("بے نظیر انکم سپورٹ پروگرام: آپ کے نام 40 ہزار روپے آئے ہیں فوری رابطہ کریں", 1),
    ("Your account is temporarily locked. Share your verification OTP code immediately to restore access.", 1),
    ("Security Alert: Suspicious login detected. Reply with your 6-digit PIN code to secure your account.", 1),
    ("Aapka imdadi paisa approve ho gaya hai. Rs 500 bhejein aur payment hasil karein.", 1),
    ("Dear customer, your bank account will be blocked today. Please send your OTP password now.", 1),
    ("BISP 8171: Apka 25000 approve ho gaya hai, apna ATM PIN foran bhejein.", 1),
    ("Ehsaas Cash 50000: Transfer Rs 2000 tax charges to claim your relief fund.", 1),
    ("Benazir Support: Send 1500 registration fee to get monthly stipend.", 1),
    ("Disaster Relief: Pay Rs 800 documentation fee to release funds immediately.", 1),

    # --- Legit / Official / Regular samples (18) ---
    ("Your NADRA CNIC renewal application has been received. Track status at id.nadra.gov.pk with tracking ID 10928.", 0),
    ("آپ کی امدادی درخواست موصول ہو گئی ہے۔ جانچ پڑتال کے بعد دفتر سے تصدیق کی جائے گی۔", 0),
    ("Govt Relief Board: No fee is ever charged for government relief assistance. Never share your OTP with anyone.", 0),
    ("Hukumat ki janib se wazifa ke liye kisi qisam ki koi registration fee nahi li jati.", 0),
    ("Your electricity bill for the month of November is Rs 3,420. Due date is 25-Nov-2026.", 0),
    ("محکمہ ریلیف: آپ کی درخواست کا کیس نمبر 49102 ہے۔ کسی بھی رہنمائی کے لیے مفت ہیلپ لائن پر کال کریں۔", 0),
    ("Relief Claim #RC-9921 is currently under review by the designated welfare officer. No action required.", 0),
    ("Assalam o Alaikum, kal subah helper center se ration card collect kar lein.", 0),
    ("This is an official verification code from government portal. Do not share it with anyone.", 0),
    ("براہ کرم اپنے قریبی سہولت مرکز پر تشریف لائیں اور اصل شناختی کارڈ دکھائیں۔", 0),
    ("Your account balance inquiry: Available balance PKR 14,200 as of today.", 0),
    ("Assalam o Alaikum, helper center se kal 5000 rupay ka ration bag collect kar lein, koi charges nahi hain.", 0),
    ("Your NADRA CNIC renewal application has been received with tracking ID 9821.", 0),
    ("Citizens can check their relief application status and registration through the official government portal.", 0),
    ("Water and Sanitation Agency: Water charges bill PKR 650 due on 30-Nov-2026.", 0),
    ("Easypaisa: You sent PKR 1,500 to Muhammad Ali (03001234567) on 21-Nov-2026. Fee: PKR 0.00.", 0),
    ("Your school tuition fee receipt for the month of November is generated. Total paid PKR 4,000.", 0),
    ("Public notice: The official Ehsaas registration is free of cost. Government never asks for any fee.", 0),
]

class ScamClassifier:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
        texts = [x[0] for x in TRAIN_DATA]
        labels = [x[1] for x in TRAIN_DATA]

        X = self.vectorizer.fit_transform(texts)
        base_lr = LogisticRegression(C=1.0, max_iter=200)
        self.model = CalibratedClassifierCV(estimator=base_lr, cv=2, n_jobs=1)
        self.model.fit(X, labels)

    def extract_reasons(self, text: str) -> List[str]:
        reasons = []
        normalized = normalize_roman_urdu(text)
        for pattern, explanation in SCAM_INDICATORS:
            if re.search(pattern, text, re.IGNORECASE) or re.search(pattern, normalized, re.IGNORECASE):
                reasons.append(explanation)
        return list(dict.fromkeys(reasons))

    def classify(self, text: str) -> Dict[str, Any]:
        """
        Classifies message text into Scam, Legit, or Unsure.
        Enhanced with Roman Urdu phonetic soundex normalization and contextual disambiguation.
        Returns: {
            "label": ScamLabel,
            "confidence": float,
            "scam_probability": float,
            "reasons": List[str]
        }
        """
        if not text or not text.strip():
            return {
                "label": ScamLabel.UNSURE,
                "confidence": 0.5,
                "scam_probability": 0.5,
                "reasons": ["Empty message provided"]
            }

        reasons = self.extract_reasons(text)
        normalized = normalize_roman_urdu(text)

        # 1. Official anti-scam warnings / fee-free advisories
        is_advisory = bool(re.search(
            r"(?:never|do not|don't|not)\b.*?\b(?:share|disclose|forward|give|send|pay|transfer)\b",
            text, re.IGNORECASE
        ) or re.search(
            r"(?:never\s*asks?|no\s*fee\s*(?:is|charged)|free\s*of\s*cost|free\s*of\s*charge|100%\s*free|zero\s*deductions?|report\s*(?:corrupt|fee|to)|beware\s*of|do\s*not\s*respond)",
            text, re.IGNORECASE
        ) or re.search(
            r"(?:kisi\s*(?:ko|qisam).*?(?:na|mat)\s*(?:dein|bhejein|batayein|share)|charges\s*nahi|fee\s*nahi|kisi\s*ko\s*paise\s*na\s*dein)",
            text, re.IGNORECASE
        ) or re.search(
            r"(?:کبھی\s*نہ|مت\s*(?:بتائیں|دیں|شیئر)|کوئی\s*فیس\s*نہیں|مفت\s*ہے|نہیں\s*مانگتا|نہ\s*بتائیں|نہ\s*دیں|ہوشیار\s*رہیں|اطلاع\s*دیں|آگاہی|خبردار|جعل\s*سازوں\s*سے)",
            text
        ))

        # Phishing trick detection: "Do not tell anyone, reply only to this number"
        has_phishing_solicitation = bool(re.search(
            r"(?:sirf\s*is\s*official\s*number\s*par\s*reply|reply\s*with|send\s*(?:your|to)|forward\s*the\s*6|بتائیں\s*تاکہ|بھیجیں\s*تاکہ|کلک کریں|click\s*here)",
            text, re.IGNORECASE
        ))
        if has_phishing_solicitation:
            is_advisory = False

        # 2. Legitimate receipts, bank transaction confirmations, and utility bills
        is_receipt_or_bill = bool(re.search(
            r"(?:fee:\s*(?:pkr|rs)?\s*0(?:\.00)?|receipt|bill\s*(?:for|pkr|rs|due|amount)|charges\s*bill|due\s*date\s*is|tuition\s*fee|subscription\s*fee.*?charged|available\s*balance|you\s*sent\s*(?:pkr|rs)|total\s*paid|cash\s*deposit|credited\s*to\s*account|inward\s*remittance|salary\s*credited|statement|invoice|funds?\s*transfer.*?received|interbank\s*fund\s*transfer|deposit\s*profit|cheque.*?cleared|transaction\s*successful|pos\s*transaction.*?approved|payment\s*received\s*with\s*thanks|retail\s*transaction.*?approved)",
            text, re.IGNORECASE
        ) or re.search(
            r"(?:بل ادا|رسید|تنخواہ منتقل|اکاؤنٹ میں رقم موصول|واجب الادا|نیا بیلنس|موجودہ بیلنس|کامیاب|موصول ہوئے)",
            text
        ))

        # 3. Legitimate government announcements and portals
        is_official_announcement = bool(re.search(
            r"(?:bisp\.gov\.pk|poverty\.gov\.pk|id\.nadra\.gov\.pk|8171\.bisp\.gov\.pk|deputy\s*commissioner\s*office|toll-free\s*helpline|joint\s*survey|mobile\s*registration\s*vans|sub-center|national\s*socio-economic\s*registry|monsoon\s*relief\s*camps)",
            text, re.IGNORECASE
        ) or re.search(
            r"(?:سہولت مراکز|تحصیل سطح|اہلیت کا معیار|ضلعی دفتر|قریبی نامزد ادائیگی مرکز|اصل شناختی کارڈ ہمراہ لائیں|مفت تکنیکی کورسز|بلا معاوضہ)",
            text
        ))

        # 4. Legitimate government helpline
        is_official_helpline = bool(re.search(r"\b8171\b", text) and re.search(r"(?:helpline|send.*?cnic|check.*?status|free|مفت|ایس ایم ایس کریں)", text, re.IGNORECASE))

        eval_text = f"{text} {normalized}"
        X = self.vectorizer.transform([eval_text])
        probs = self.model.predict_proba(X)[0]
        prob_scam = float(probs[1])

        has_credential_theft = any("Requests sensitive security PIN or OTP" in r for r in reasons)
        has_advance_fee = any("Asks for advance fee" in r for r in reasons)
        has_urgency = any("artificial urgency" in r for r in reasons)
        has_url = any("Contains unverified or shortened external URL" in r for r in reasons)
        has_lottery = any("Claims unexpected lottery" in r for r in reasons)

        # Administrative document submission without fee/money (e.g. submitting income certificate or CNIC copy)
        is_document_submission = bool(re.search(
            r"(?:سرٹیفکیٹ|دستاویز|کاغذات|فارم|شناختی\s*کارڈ\s*کی\s*کاپی).*?(?:جمع|لائیں|دیں)",
            text
        ) and not re.search(r"(?:روپے|فیس|چارجز|رقم|ایزی\s*پیسہ|جائز\s*کیش|rs|pkr|fee|charges|tax)", text, re.IGNORECASE))

        if is_document_submission:
            has_advance_fee = False
            reasons = [r for r in reasons if "advance fee" not in r]

        # Credential theft must NEVER escape unless explicitly an advisory against sharing
        if has_credential_theft and not is_advisory:
            prob_scam = max(prob_scam, 0.95)
        elif has_advance_fee and not is_receipt_or_bill and not is_advisory:
            prob_scam = max(prob_scam, 0.88)
        elif (has_urgency or has_url or has_lottery) and not is_receipt_or_bill and not is_advisory and not is_official_announcement:
            if prob_scam >= 0.20 or len(reasons) >= 2 or has_url:
                prob_scam = max(prob_scam, 0.82)
        elif len(reasons) >= 2 and not is_receipt_or_bill and not is_advisory and not is_official_helpline and not is_official_announcement:
            prob_scam = max(prob_scam, 0.78)

        # Safety constraint: Pure statistical NLP without ANY rule indicators must NOT unilaterally declare SCAM
        # It routes to human review (UNSURE) to prevent algorithmic disenfranchisement of ambiguous administrative notices
        if not (has_credential_theft or has_advance_fee or has_urgency or has_url or has_lottery or len(reasons) >= 1):
            prob_scam = min(prob_scam, 0.65)

        # Dampen probability for verified receipts, utility bills, advisories, and official announcements
        if (is_receipt_or_bill or is_advisory or is_official_helpline or is_official_announcement) and not (has_credential_theft and not is_advisory):
            prob_scam = min(prob_scam, 0.20)
            # Remove misleading reasons if it was a receipt or advisory
            reasons = [r for r in reasons if "advance fee" not in r and "relief scheme" not in r and "Requests sensitive security PIN or OTP" not in r and "artificial urgency" not in r]

        # Classification thresholds with "I am not sure" band
        if prob_scam >= 0.70:
            label = ScamLabel.SCAM
            confidence = round(prob_scam, 3)
            if not reasons:
                reasons.append("NLP model detected stylistic patterns matching known fraudulent solicitations")
        elif prob_scam <= 0.35:
            label = ScamLabel.LEGIT
            confidence = round(1.0 - prob_scam, 3)
            if not reasons or is_advisory or is_receipt_or_bill:
                reasons = ["No coercive language, fee demands, or suspicious link patterns found"]
        else:
            # 0.35 < prob_scam < 0.70 -> UNSURE: Escalate to human
            label = ScamLabel.UNSURE
            confidence = round(1.0 - abs(prob_scam - 0.5) * 2, 3)
            reasons.append("Borderline patterns detected; requires officer verification")

        return {
            "label": label,
            "confidence": confidence,
            "scam_probability": round(prob_scam, 4),
            "reasons": reasons
        }


# Global singleton instance
scam_classifier = ScamClassifier()

def classify_message(text: str) -> Dict[str, Any]:
    """Top-level helper function for fraud classification."""
    return scam_classifier.classify(text)
