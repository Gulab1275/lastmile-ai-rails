"""
Detailed breakdown of the 300 Holdout Benchmark by Language and Category 10 Analysis.
"""
import os
import sys
import re
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.ai.scam import classify_message
from services.shared.schemas import ScamLabel
from scripts.eval_scam_holdout_300 import HOLDOUT_300


def detect_language(text: str) -> str:
    # Check for Arabic/Urdu unicode range
    urdu_chars = len(re.findall(r'[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]', text))
    if urdu_chars > 3:
        return "Urdu"
    # Check for common Roman Urdu tokens
    roman_urdu_words = {"aap", "aapki", "apka", "bhai", "mein", "hain", "karein", "rupay", "paise", "mile", "milenge", "hukumat", "wazifa", "tashreef", "lekin", "nahi", "raha", "gaya", "jae", "dein"}
    tokens = set(re.findall(r'[a-zA-Z]+', text.lower()))
    if len(tokens.intersection(roman_urdu_words)) >= 2:
        return "Roman Urdu"
    return "English"


def main():
    print("=" * 80)
    print("1. ANALYSIS OF CATEGORY 10 (AMBIGUOUS / BORDERLINE SOLICITATIONS - 30 MSGS)")
    print("=" * 80)
    
    cat10 = HOLDOUT_300[270:]
    scam_count = 0
    legit_count = 0
    unsure_count = 0

    for idx, (text, label) in enumerate(cat10, 1):
        res = classify_message(text)
        pred = res["label"].value.upper()
        prob = res.get("scam_probability", 0.0)
        reasons = res.get("reasons", [])
        if pred == "SCAM":
            scam_count += 1
            print(f"[PRED: SCAM  ] #{idx}: prob={prob:.2f} | reasons={reasons}")
            print(f"   Text: \"{text}\"\n")
        elif pred == "LEGIT":
            legit_count += 1
            print(f"[PRED: LEGIT ] #{idx}: prob={prob:.2f} | reasons={reasons}")
            print(f"   Text: \"{text}\"\n")
        else:
            unsure_count += 1
            print(f"[PRED: UNSURE] #{idx}: prob={prob:.2f} | reasons={reasons}")
            print(f"   Text: \"{text}\"\n")

    print(f"Category 10 Summary: SCAM={scam_count}, LEGIT={legit_count}, UNSURE={unsure_count} (Total: {len(cat10)})")

    print("\n" + "=" * 80)
    print("2. CONFUSION MATRIX BY LANGUAGE (Urdu, Roman Urdu, English)")
    print("=" * 80)

    by_lang = defaultdict(lambda: {"SCAM": defaultdict(int), "LEGIT": defaultdict(int), "UNSURE": defaultdict(int)})
    lang_totals = defaultdict(int)

    for text, truth in HOLDOUT_300:
        lang = detect_language(text)
        lang_totals[lang] += 1
        res = classify_message(text)
        pred = res["label"].value.upper()
        by_lang[lang][truth][pred] += 1

    for lang in ["Urdu", "Roman Urdu", "English"]:
        print(f"\n--- LANGUAGE: {lang} (Total: {lang_totals[lang]} messages) ---")
        print(f"{'Ground Truth':<15} | {'Pred SCAM':<12} | {'Pred LEGIT':<12} | {'Pred UNSURE':<12} | {'Total':<8}")
        print("-" * 65)
        for truth in ["SCAM", "LEGIT", "UNSURE"]:
            row = by_lang[lang][truth]
            tot = sum(row.values())
            print(f"{truth:<15} | {row['SCAM']:<12} | {row['LEGIT']:<12} | {row['UNSURE']:<12} | {tot:<8}")

        # Metrics for this language
        scams = by_lang[lang]["SCAM"]
        legits = by_lang[lang]["LEGIT"]
        tot_scams = sum(scams.values())
        tot_legits = sum(legits.values())
        
        recall = (scams["SCAM"] / tot_scams * 100) if tot_scams > 0 else 0
        fpr = (legits["SCAM"] / tot_legits * 100) if tot_legits > 0 else 0
        fnr = (scams["LEGIT"] / tot_scams * 100) if tot_scams > 0 else 0
        unsure_legit = (legits["UNSURE"] / tot_legits * 100) if tot_legits > 0 else 0

        print(f"Metrics ({lang}): Recall={recall:.1f}%, FPR={fpr:.1f}%, FNR={fnr:.1f}%, Legit Routed to Unsure={unsure_legit:.1f}%")


if __name__ == "__main__":
    main()
