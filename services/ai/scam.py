"""
Probabilistic Scam and Phishing Classifier (Challenge 08: Scams and Fake Documents).
Detects fake relief cash offers, OTP theft, and phishing links in Urdu, Roman Urdu, and English.
Uses scikit-learn TF-IDF + Calibrated Logistic Regression + Explainable Rule Features.
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
    (r"(otp|pin|password|کوڈ|پاسورڈ)", "Requests sensitive security PIN or OTP"),
    (r"(fee|advance|charges|tax|فیس|ایڈوانس|رقم جمع)", "Asks for advance fee or payment to release relief funds"),
    (r"(hurry|urgent|immediate|last chance|آخری تاریخ|جلدی کریں|فوری)", "Uses high-pressure artificial urgency"),
    (r"(http://|https://|bit\.ly|t\.co|wa\.me|tinyurl|goo\.gl)", "Contains unverified or shortened external URL"),
    (r"(won|lottery|lucky draw|انعام|لاٹری|قرعہ اندازی)", "Claims unexpected lottery or lucky draw win"),
    (r"(8171|bisp|ehsaas|benazir|احساس|بینظیر)", "Mentions government relief scheme without official domain verification")
]

# Baseline training corpus (English, Urdu, Roman Urdu)
TRAIN_DATA = [
    # --- Scam samples ---
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

    # --- Legit / Official / Regular samples ---
    ("Your NADRA CNIC renewal application has been received. Track status at id.nadra.gov.pk with tracking ID 10928.", 0),
    ("آپ کی امدادی درخواست موصول ہو گئی ہے۔ جانچ پڑتال کے بعد دفتر سے تصدیق کی جائے گی۔", 0),
    ("Govt Relief Board: No fee is ever charged for government relief assistance. Never share your OTP with anyone.", 0),
    ("Hukumat ki janib se wazifa ke liye kisi qisam ki koi registration fee nahi li jati.", 0),
    ("Your electricity bill for the month of November is Rs 3,420. Due date is 25-Nov-2026.", 0),
    ("محکمہ ریلیف: آپ کی درخواست کا کیس نمبر 49102 ہے۔ کسی بھی رہنمائی کے لیے مفت ہیلپ لائن پر کال کریں۔", 0),
    ("Relief Claim #RC-9921 is currently under review by the designated welfare officer. No action required.", 0),
    ("Assalam o Alaikum, kal subah helper center se ration card collect kar lein.", 0),
    ("This is an official verification code from government portal. Do not share it with anyone.", 0),
    ("براہ کرم اپنے قریبی سہولت مرکز پر تشریف لائیں اور اصل شناختی کارڈ دکھائیں۔", 0)
]

class ScamClassifier:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
        texts = [x[0] for x in TRAIN_DATA]
        labels = [x[1] for x in TRAIN_DATA]

        X = self.vectorizer.fit_transform(texts)
        base_lr = LogisticRegression(C=1.0, max_iter=200)
        self.model = CalibratedClassifierCV(estimator=base_lr, cv=2)
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
        Enhanced with Roman Urdu phonetic soundex normalization.
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
        eval_text = f"{text} {normalized}"
        X = self.vectorizer.transform([eval_text])
        probs = self.model.predict_proba(X)[0]
        prob_scam = float(probs[1])

        # Rule boosting: If urgent + asks for fee/OTP, high confidence scam
        if len(reasons) >= 2 and prob_scam >= 0.4:
            prob_scam = min(0.98, prob_scam + 0.35)

        # Classification thresholds with "I am not sure" band
        if prob_scam >= 0.70:
            label = ScamLabel.SCAM
            confidence = round(prob_scam, 3)
            if not reasons:
                reasons.append("NLP model detected stylistic patterns matching known fraudulent solicitations")
        elif prob_scam <= 0.30:
            label = ScamLabel.LEGIT
            confidence = round(1.0 - prob_scam, 3)
            reasons = ["No coercive language, fee demands, or suspicious link patterns found"]
        else:
            # 0.30 < prob_scam < 0.70 -> UNSURE: Escalate to human
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
_scam_classifier = ScamClassifier()

def classify_message(text: str) -> Dict[str, Any]:
    """Public function exposed to API."""
    return _scam_classifier.classify(text)
