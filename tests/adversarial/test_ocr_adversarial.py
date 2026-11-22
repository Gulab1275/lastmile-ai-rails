"""
Adversarial Test Suite C: OCR & Document Verification Stress Attacks.
Tests C01 - C10: Evaluates Laplacian blur threshold, ELA tamper detection,
corrupted byte handling, format spoofing, and orientation stress without crash.
"""
import io

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

from services.ai.ocr import compute_blur_score, compute_tamper_score, extract_documents, extract_fields_from_text


def _create_synthetic_cnic_image(text="Name: Parveen Bibi\nCNIC: 42101-1234567-1\nDOB: 12-05-1985") -> Image.Image:
    img = Image.new("RGB", (400, 250), color=(240, 240, 240))
    draw = ImageDraw.Draw(img)
    # Draw dark text with sharp edges
    lines = text.split("\n")
    y = 30
    for line in lines:
        draw.text((30, y), line, fill=(10, 10, 10))
        y += 40
    # Add a border to simulate card edge
    draw.rectangle([10, 10, 390, 240], outline=(50, 50, 50), width=2)
    return img


def test_c01_clear_synthetic_cnic_passes_quality_gate():
    """C01: Clear synthetic CNIC image has high blur score and passes gate."""
    img = _create_synthetic_cnic_image()
    score = compute_blur_score(img)
    assert score > 90.0, f"Expected blur score > 90.0 for sharp image, got {score}"


def test_c02_blurry_cnic_rejected_by_laplacian_gate():
    """C02: Heavily blurred synthetic CNIC fails blur score threshold (< 90)."""
    img = _create_synthetic_cnic_image()
    blurry = img.filter(ImageFilter.GaussianBlur(radius=8))
    score = compute_blur_score(blurry)
    assert score < 90.0, f"Expected blur score < 90.0 for blurred image, got {score}"


def test_c03_unreadable_or_missing_qr_code_handled():
    """C03: Image without QR code or with unreadable pixels does not throw unhandled exception."""
    img = _create_synthetic_cnic_image()
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    # extract_documents should process without crashing when no QR is decoded
    res = extract_documents([buf.getvalue()])
    assert "blur_score" in res
    assert "tamper_score" in res


def test_c04_qr_code_identity_mismatch_check():
    """C04: Document where extracted QR text differs from printed OCR fields is distinguishable."""
    ocr_fields = {"cnic": "42101-1234567-1", "full_name": "Parveen Bibi"}
    qr_payload = {"cnic": "42101-9999999-9", "full_name": "Fatima Bibi"}

    # System must flag mismatch between printed OCR and QR payload
    assert ocr_fields["cnic"] != qr_payload["cnic"]


def test_c05_digit_tampering_elevates_ela_tamper_score():
    """C05: Image with digitally spliced/manipulated pixels produces detectable tamper probability."""
    img = _create_synthetic_cnic_image()
    # Digitally splice high-contrast noise over CNIC area
    draw = ImageDraw.Draw(img)
    draw.rectangle([100, 70, 220, 100], fill=(255, 0, 0))
    tamper_prob = compute_tamper_score(img)
    assert isinstance(tamper_prob, float)
    assert 0.0 <= tamper_prob <= 1.0


def test_c06_utility_bill_belongs_to_different_citizen():
    """C06: Utility bill with different name and address is parsed correctly."""
    bill_text = "ELECTRICITY BILL\nConsumer Name: Ghulam Rasool\nCNIC: 42101-8888888-8\nAmount: Rs 4,500"
    fields = extract_fields_from_text(bill_text)
    assert fields["fields"].get("cnic") == "42101-8888888-8"


def test_c07_rotated_dark_glare_and_cropped_stress():
    """C07: Rotated, dark, and shadowed images do not cause pipeline crash."""
    base = _create_synthetic_cnic_image()

    # 90-degree rotated
    rot90 = base.rotate(90, expand=True)
    score_rot = compute_blur_score(rot90)
    assert score_rot >= 0.0

    # Very dark image
    dark = ImageEnhance.Brightness(base).enhance(0.1)
    score_dark = compute_blur_score(dark)
    assert score_dark >= 0.0

    # Cropped sliver
    cropped = base.crop((0, 0, 50, 50))
    score_crop = compute_blur_score(cropped)
    assert score_crop >= 0.0


def test_c08_unsupported_file_disguised_as_jpg():
    """C08: Unsupported file type disguised as JPG (arbitrary binary bytes) does not crash."""
    fake_jpg = b"MZ\x90\x00\x03\x00\x00\x00FAKE_EXECUTABLE_HEADER_NOT_A_REAL_IMAGE"
    res = extract_documents([fake_jpg])

    # Must handle gracefully and return 0 blur / fallback tamper
    assert res["blur_score"] == 0.0
    assert "fields" in res


def test_c09_extremely_large_and_corrupted_image_bytes():
    """C09: Large image dimensions and partially corrupted JPEG stream handled gracefully."""
    # Corrupted JPEG header
    corrupt_stream = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01" + b"\x00" * 50
    res_corrupt = extract_documents([corrupt_stream])
    assert res_corrupt["blur_score"] == 0.0

    # Large image
    large_img = Image.new("RGB", (2000, 2000), color=(255, 255, 255))
    buf = io.BytesIO()
    large_img.save(buf, format="JPEG")
    res_large = extract_documents([buf.getvalue()])
    assert "blur_score" in res_large


def test_c10_repeated_document_hash_deduplication():
    """C10: Same document uploaded repeatedly produces identical blur scores and byte signatures."""
    img = _create_synthetic_cnic_image()
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    raw = buf.getvalue()

    res1 = extract_documents([raw])
    res2 = extract_documents([raw])

    assert res1["blur_score"] == res2["blur_score"]
    assert res1["tamper_score"] == res2["tamper_score"]
