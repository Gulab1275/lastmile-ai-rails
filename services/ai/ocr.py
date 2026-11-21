"""
Document OCR & Authenticity Pipeline (Challenge 08: Scams and Fake Documents).
Performs:
1. Laplacian blur detection (gates unreadable / blurry submissions).
2. Tesseract OCR with regex field extraction (CNIC, Name, DOB).
3. Digital tampering & Error-Level Analysis (ELA) estimation.
"""
import io
import re
from typing import Any, Dict, List

import numpy as np
from PIL import Image, ImageChops, ImageEnhance

try:
    import pytesseract
except ImportError:
    pytesseract = None

BLUR_THRESHOLD = 90.0

def compute_blur_score(image: Image.Image) -> float:
    """
    Computes Laplacian variance of grayscale image to measure sharpness.
    Scores < 90 indicate blurry images.
    """
    gray = image.convert("L")
    arr = np.array(gray, dtype=np.float64)
    if arr.shape[0] < 3 or arr.shape[1] < 3:
        return 0.0

    # 3x3 Discrete Laplacian kernel
    laplacian = (
        -4 * arr[1:-1, 1:-1]
        + arr[:-2, 1:-1]
        + arr[2:, 1:-1]
        + arr[1:-1, :-2]
        + arr[1:-1, 2:]
    )
    variance = float(np.var(laplacian))
    return round(variance, 2)

def compute_tamper_score(image: Image.Image) -> float:
    """
    Error Level Analysis (ELA): Compares original image with a 90% recompressed version.
    Inconsistent high-contrast difference blocks indicate digital manipulation or spliced text.
    """
    try:
        # Save at 90% JPEG quality
        buf = io.BytesIO()
        image.convert("RGB").save(buf, format="JPEG", quality=90)
        buf.seek(0)
        recompressed = Image.open(buf)

        # Difference
        diff = ImageChops.difference(image.convert("RGB"), recompressed)
        extrema = diff.getextrema()
        max_diff = max([ex[1] for ex in extrema])
        scale = 255.0 / max(max_diff, 1)
        diff = ImageEnhance.Brightness(diff).enhance(scale)

        diff_arr = np.array(diff.convert("L"), dtype=np.float64)
        mean_diff = float(np.mean(diff_arr))

        # Normalized tamper score between 0.0 and 1.0
        tamper_prob = min(1.0, mean_diff / 50.0)
        return round(tamper_prob, 3)
    except Exception:
        return 0.05

def extract_fields_from_text(text: str) -> Dict[str, Any]:
    """Extracts structured CNIC, Name, and DOB using regular expressions."""
    fields = {}
    confidences = {}

    # CNIC match
    cnic_match = re.search(r"\b\d{5}[-\s]?\d{7}[-\s]?\d{1}\b", text)
    if cnic_match:
        raw_cnic = re.sub(r"\D", "", cnic_match.group(0))
        fields["cnic"] = f"{raw_cnic[:5]}-{raw_cnic[5:12]}-{raw_cnic[12]}"
        confidences["cnic"] = 0.95

    # DOB match
    dob_match = re.search(r"\b(\d{2}[./-]\d{2}[./-]\d{4})\b", text)
    if dob_match:
        fields["dob"] = dob_match.group(1).replace("/", "-").replace(".", "-")
        confidences["dob"] = 0.90

    # Name match heuristic (Urdu or English)
    name_match = re.search(r"(?:Name|نام)[:\s]+([A-Za-z\s]{3,30})", text, re.IGNORECASE)
    if name_match:
        fields["full_name"] = name_match.group(1).strip()
        confidences["full_name"] = 0.85

    return {"fields": fields, "field_confidences": confidences}

def extract_documents(files: List[bytes]) -> Dict[str, Any]:
    """
    Public AI function: extracts fields, blur score, and tamper score from uploaded documents.
    """
    if not files:
        return {
            "fields": {},
            "field_confidences": {},
            "blur_score": 0.0,
            "is_blurry": True,
            "tamper_score": 0.0,
            "text": ""
        }

    merged_fields = {}
    merged_confidences = {}
    blur_scores = []
    tamper_scores = []
    all_text = []

    for file_bytes in files:
        try:
            image = Image.open(io.BytesIO(file_bytes))

            # 1. Blur check
            b_score = compute_blur_score(image)
            blur_scores.append(b_score)

            # 2. Tamper check
            t_score = compute_tamper_score(image)
            tamper_scores.append(t_score)

            # 3. OCR extraction (with fallback if tesseract executable missing)
            try:
                ocr_text = pytesseract.image_to_string(image, lang="eng+urd")
            except Exception:
                ocr_text = ""

            all_text.append(ocr_text)
            extracted = extract_fields_from_text(ocr_text)
            merged_fields.update(extracted["fields"])
            merged_confidences.update(extracted["field_confidences"])

        except Exception as e:
            print(f"Error processing document: {e}")

    avg_blur = round(float(np.mean(blur_scores)), 2) if blur_scores else 0.0
    max_tamper = round(float(np.max(tamper_scores)), 3) if tamper_scores else 0.0
    is_blurry = avg_blur < BLUR_THRESHOLD

    return {
        "fields": merged_fields,
        "field_confidences": merged_confidences,
        "blur_score": avg_blur,
        "is_blurry": is_blurry,
        "tamper_score": max_tamper,
        "raw_text": "\n".join(all_text)
    }
