import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.eval_scam_300_preprod import EVALUATION_DATASET
from services.ai.scam import classify_message

print("=== SCAMS MISCLASSIFIED AS LEGIT (CRITICAL VULNERABILITY) ===")
for text, actual, cat in EVALUATION_DATASET:
    if actual == "SCAM":
        res = classify_message(text)
        if res["label"].value.upper() == "LEGIT":
            print(f"Category: {cat}")
            print(f"Text: {text}")
            print(f"Prob: {res['scam_probability']}, Reasons: {res['reasons']}")
            print("-" * 50)

print("\n=== LEGIT MISCLASSIFIED AS SCAM (FALSE POSITIVES) ===")
for text, actual, cat in EVALUATION_DATASET:
    if actual == "LEGIT":
        res = classify_message(text)
        if res["label"].value.upper() == "SCAM":
            print(f"Category: {cat}")
            print(f"Text: {text}")
            print(f"Prob: {res['scam_probability']}, Reasons: {res['reasons']}")
            print("-" * 50)
