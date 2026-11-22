import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.eval_scam_holdout_300 import HOLDOUT_300
from services.ai.scam import classify_message

print("=== MISCLASSIFIED OTP (indices 90..119) ===")
for i in range(90, 120):
    t, true_y = HOLDOUT_300[i]
    res = classify_message(t)
    lbl = res["label"].value.upper()
    if lbl != "SCAM":
        print(f"Index {i}: {lbl} (prob: {res['scam_probability']}, reasons: {res['reasons']})")
        print(f"Text: {t}\n")

print("\n=== FALSE POSITIVES (True LEGIT predicted as SCAM) ===")
for i, (t, true_y) in enumerate(HOLDOUT_300):
    if true_y == "LEGIT":
        res = classify_message(t)
        lbl = res["label"].value.upper()
        if lbl == "SCAM":
            print(f"Index {i}: prob {res['scam_probability']}, reasons: {res['reasons']}")
            print(f"Text: {t}\n")

print("\n=== FALSE NEGATIVES (True SCAM predicted as LEGIT) ===")
for i, (t, true_y) in enumerate(HOLDOUT_300):
    if true_y == "SCAM":
        res = classify_message(t)
        lbl = res["label"].value.upper()
        if lbl == "LEGIT":
            print(f"Index {i}: prob {res['scam_probability']}, reasons: {res['reasons']}")
            print(f"Text: {t}\n")

print("\n=== SCAMS PREDICTED AS UNSURE ===")
for i, (t, true_y) in enumerate(HOLDOUT_300):
    if true_y == "SCAM":
        res = classify_message(t)
        lbl = res["label"].value.upper()
        if lbl == "UNSURE":
            print(f"Index {i}: prob {res['scam_probability']}, reasons: {res['reasons']}")
            print(f"Text: {t[:80]}...\n")
