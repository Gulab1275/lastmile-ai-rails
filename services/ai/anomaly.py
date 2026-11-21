"""
Anomaly Detection Engine (Task N13 / Creative AI Rails).
Detects repeat claim patterns, helper submission velocity spikes,
income-to-request outliers, and fraudulent duplicate assistance.

Implements:
1. Deterministic pattern checks (repeat phone, duplicate household, helper velocity).
2. Machine Learning statistical outlier detection using IsolationForest on multidimensional claim feature vectors.
3. Dual-language explanations (English and Urdu) for auditors and case officers.
"""

from typing import Any, Dict, List, Optional

import numpy as np
from sklearn.ensemble import IsolationForest

# Calibrated IsolationForest baseline
_BASELINE_TRAINING_DATA = np.array([
    # [requested_amount, monthly_income, ratio, household_size, amount_per_capita, velocity_24h, tamper_score]
    [8000, 18000, 0.44, 4, 2000, 2, 0.02],
    [10000, 22000, 0.45, 5, 2000, 3, 0.01],
    [12000, 25000, 0.48, 6, 2000, 1, 0.00],
    [15000, 30000, 0.50, 6, 2500, 4, 0.05],
    [8000, 15000, 0.53, 3, 2666, 1, 0.02],
    [10000, 20000, 0.50, 4, 2500, 2, 0.04],
    [12000, 28000, 0.42, 5, 2400, 2, 0.01],
    [15000, 35000, 0.42, 7, 2142, 3, 0.03],
    [9000, 19000, 0.47, 4, 2250, 1, 0.00],
    [11000, 24000, 0.45, 5, 2200, 2, 0.02],
    [14000, 32000, 0.43, 6, 2333, 3, 0.01],
    [10000, 16000, 0.62, 5, 2000, 2, 0.03],
    [8000, 12000, 0.66, 4, 2000, 1, 0.01],
    [15000, 38000, 0.39, 7, 2142, 4, 0.02],
    [12000, 27000, 0.44, 5, 2400, 2, 0.01],
    # Edge normal cases
    [18000, 42000, 0.42, 8, 2250, 5, 0.06],
    [6000, 10000, 0.60, 3, 2000, 1, 0.01],
    [10000, 25000, 0.40, 4, 2500, 2, 0.00],
    [12000, 29000, 0.41, 5, 2400, 3, 0.02],
    [15000, 33000, 0.45, 6, 2500, 2, 0.01],
])

# Initialize and fit singleton IsolationForest
_ISO_FOREST = IsolationForest(
    n_estimators=100,
    contamination=0.08,
    random_state=42
)
_ISO_FOREST.fit(_BASELINE_TRAINING_DATA)


def extract_claim_features(claim: Dict[str, Any]) -> np.ndarray:
    """Extracts numeric feature vector from claim data."""
    requested_amount = float(claim.get("requested_amount") or 10000.0)
    monthly_income = float(claim.get("monthly_income") or 25000.0)
    ratio = requested_amount / max(monthly_income, 1.0)
    household_size = max(int(claim.get("household_size") or 4), 1)
    amount_per_capita = requested_amount / household_size
    velocity_24h = float(claim.get("helper_velocity_24h") or 1.0)
    tamper_score = float(claim.get("tamper_score") or 0.0)

    return np.array([
        requested_amount,
        monthly_income,
        ratio,
        household_size,
        amount_per_capita,
        velocity_24h,
        tamper_score
    ])


def detect_claim_anomalies(
    claim: Dict[str, Any],
    historical_claims: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Evaluates a claim for suspicious patterns, duplicate assistance,
    unusual velocity, and statistical outliers.
    """
    flags: List[str] = []
    reasons_en: List[str] = []
    reasons_ur: List[str] = []

    # 1. Deterministic Heuristics
    cnic = str(claim.get("cnic", "")).strip()
    phone = str(claim.get("phone", "")).strip().replace("-", "").replace(" ", "")
    claim.get("helper_id")
    requested_amount = float(claim.get("requested_amount") or 10000.0)
    monthly_income = float(claim.get("monthly_income") or 25000.0)
    helper_velocity = int(claim.get("helper_velocity_24h") or 1)

    # Ratio Check: Claim amount exceeding monthly income
    if monthly_income > 0 and (requested_amount / monthly_income) > 1.2:
        flags.append("SUSPICIOUS_INCOME_TO_CLAIM_RATIO")
        reasons_en.append(f"Requested amount (PKR {requested_amount:,.0f}) exceeds 120% of declared monthly income (PKR {monthly_income:,.0f}).")
        reasons_ur.append("درخواست کردہ رقم ماہانہ آمدنی کے 120 فیصد سے زیادہ ہے۔")

    # Helper Velocity Check
    if helper_velocity > 15:
        flags.append("HIGH_VELOCITY_HELPER")
        reasons_en.append(f"Helper submitted {helper_velocity} claims within 24 hours, exceeding normal operational velocity.")
        reasons_ur.append("مددگار نے 24 گھنٹوں میں غیر معمولی طور پر زیادہ درخواستیں جمع کرائیں۔")

    # Repeat / Duplicate Check against historical claims
    if historical_claims:
        phone_matches = 0
        cnic_matches = 0
        current_case_id = claim.get("case_id")

        for hist in historical_claims:
            if hist.get("case_id") == current_case_id:
                continue

            hist_phone = str(hist.get("phone", "")).strip().replace("-", "").replace(" ", "")
            hist_cnic = str(hist.get("cnic", "")).strip()

            if phone and hist_phone and phone == hist_phone:
                phone_matches += 1
            if cnic and hist_cnic and cnic == hist_cnic:
                cnic_matches += 1

        if cnic_matches > 0:
            flags.append("REPEAT_CNIC_CLAIM")
            reasons_en.append(f"CNIC {cnic} already has {cnic_matches} active or previous claim(s) in system.")
            reasons_ur.append("اس شناختی کارڈ پر پہلے سے امدادی درخواست ریکارڈ پر موجود ہے۔")

        if phone_matches >= 3:
            flags.append("REPEAT_PHONE_BURST")
            reasons_en.append(f"Phone {phone} is associated with {phone_matches} different historical claims.")
            reasons_ur.append("یہ موبائل نمبر ایک سے زیادہ مختلف افراد کی درخواستوں میں استعمال ہو رہا ہے۔")

    # 2. Machine Learning Outlier Detection (IsolationForest)
    features = extract_claim_features(claim)
    features_2d = features.reshape(1, -1)

    # isolation forest decision_function: lower means more abnormal
    raw_score = float(_ISO_FOREST.decision_function(features_2d)[0])
    prediction = int(_ISO_FOREST.predict(features_2d)[0])  # -1 is anomaly, 1 is inlier

    # Calibrate raw_score (typically in range [-0.3, +0.2]) to risk score in [0.0, 1.0]
    # score < 0 indicates anomaly
    calibrated_risk = float(np.clip(1.0 - (raw_score + 0.2) / 0.4, 0.0, 1.0))

    if prediction == -1 or calibrated_risk >= 0.70:
        if "OUTLIER_CLAIM_PROFILE" not in flags:
            flags.append("OUTLIER_CLAIM_PROFILE")
            reasons_en.append(f"IsolationForest flagged statistical outlier in feature combination (anomaly risk: {calibrated_risk:.2f}).")
            reasons_ur.append("شماریاتی تجزیے کے مطابق اس کیس کا ڈیٹا معمول سے غیر معمولی طور پر مختلف ہے۔")

    is_anomaly = (len(flags) > 0) or (prediction == -1)
    # Overall anomaly score combines calibrated ML risk with rule flags
    overall_anomaly_score = max(calibrated_risk, 0.85 if len(flags) >= 2 else (0.55 if len(flags) == 1 else calibrated_risk))
    overall_anomaly_score = round(float(np.clip(overall_anomaly_score, 0.0, 1.0)), 3)

    return {
        "is_anomaly": is_anomaly,
        "anomaly_score": overall_anomaly_score,
        "flags": flags,
        "reasons_en": reasons_en if reasons_en else ["No anomalous patterns detected in claim profile."],
        "reasons_ur": reasons_ur if reasons_ur else ["کیس میں کوئی غیر معمولی یا مشکوک پیٹرن نہیں پایا گیا۔"],
        "metrics": {
            "raw_isolation_score": round(raw_score, 4),
            "calibrated_risk": round(calibrated_risk, 4),
            "features_analyzed": {
                "requested_amount": features[0],
                "monthly_income": features[1],
                "income_ratio": round(features[2], 2),
                "household_size": int(features[3]),
                "amount_per_capita": round(features[4], 1),
                "helper_velocity_24h": int(features[5]),
                "tamper_score": round(features[6], 3),
            }
        }
    }
