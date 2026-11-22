"""
Test Refinements for Scam Classifier.
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.eval_scam_holdout_300 import HOLDOUT_300
from services.ai.scam import scam_classifier
from services.shared.schemas import ScamLabel


def test_proposed_heuristic():
    print("Testing proposed heuristic on 300 Holdout Messages...")
    
    # We will temporarily test the logic
    matrix = {"SCAM": {"SCAM": 0, "LEGIT": 0, "UNSURE": 0},
              "LEGIT": {"SCAM": 0, "LEGIT": 0, "UNSURE": 0},
              "UNSURE": {"SCAM": 0, "LEGIT": 0, "UNSURE": 0}}
    
    otp_total = 0
    otp_detected = 0

    for idx, (text, true_str) in enumerate(HOLDOUT_300):
        res = scam_classifier.classify(text)
        pred = res["label"].value.upper()
        
        # Check OTP
        if 90 <= idx < 120:
            otp_total += 1
            if pred == "SCAM":
                otp_detected += 1
                
        matrix[true_str][pred] += 1

    print("Baseline Matrix:")
    for t in ["SCAM", "LEGIT", "UNSURE"]:
        print(f"{t}: {dict(matrix[t])}")

    scam_recall = matrix["SCAM"]["SCAM"] / sum(matrix["SCAM"].values()) * 100
    scam_prec = matrix["SCAM"]["SCAM"] / (matrix["SCAM"]["SCAM"] + matrix["LEGIT"]["SCAM"] + matrix["UNSURE"]["SCAM"]) * 100
    fpr = matrix["LEGIT"]["SCAM"] / sum(matrix["LEGIT"].values()) * 100
    fnr = matrix["SCAM"]["LEGIT"] / sum(matrix["SCAM"].values()) * 100
    otp_recall = otp_detected / otp_total * 100

    print(f"Scam Recall: {scam_recall:.2f}%")
    print(f"Scam Precision: {scam_prec:.2f}%")
    print(f"FPR: {fpr:.2f}%")
    print(f"FNR: {fnr:.2f}%")
    print("\n--- Scams routed to UNSURE (Human Review) ---")
    for idx, (text, true_str) in enumerate(HOLDOUT_300[:150]):
        res = scam_classifier.classify(text)
        if res["label"].value.upper() == "UNSURE":
            print(f"Scam #{idx+1} routed to UNSURE: {res['reasons']} -> \"{text[:65]}\"")
    msgs = [
        "Apka token number 109 hai, subah 9 baje tehsil office tashreef layen.",
        "Apka cnic record verify ho raha hai, mazeed maloomat k liye portal visit karein.",
        "Community elder meeting regarding local relief allocation will take place tomorrow at union council.",
        "Apka family size record 5 afrad par mushtamil darj kiya gaya hai.",
        "آپ کی فائل میں آمدنی کا سرٹیفکیٹ مطلوب ہے، جلد از جلد دفتر جمع کروائیں۔"
    ]
    for m in msgs:
        reasons = scam_classifier.extract_reasons(m)
        print(f"Msg: \"{m[:45]}\" -> Reasons: {reasons}")


if __name__ == "__main__":
    test_proposed_heuristic()
