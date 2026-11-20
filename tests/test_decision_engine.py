"""
Tests for Decision Engine, Weakest-Link Confidence, and Cost Matrix Thresholds.
Implements:
- Principle 1: The LLM never makes the approval decision.
- Principle 2: Confidence is min(components).
- Principle 3: The system never auto-rejects.
- Challenge 01: The Cost of Being Wrong (cost matrix thresholds).
"""
from services.api.engine.decision_engine import DecisionEngine
from services.shared.schemas import ComponentScores, RouteDecision


def test_weakest_link_confidence_calculation():
    """
    CRITICAL HACKATHON PRINCIPLE:
    Confidence is the weakest link, NOT the average!
    min(1.0, 1.0, 1.0, 1.0, 0.40) must be 0.40.
    """
    engine = DecisionEngine()
    scores = ComponentScores(
        identity=0.98,
        ocr=0.95,
        authenticity=0.99,
        rules_complete=0.90,
        scam_safety=0.35  # Weakest link!
    )
    case_data = {"monthly_income": 20000.0, "requested_amount": 10000.0, "household_size": 3}
    decision = engine.evaluate_case("cas_test_1", case_data, scores)

    assert decision.confidence == 0.35
    # Since confidence is 0.35 (p_wrong = 0.65 > 0.30), it must route to Human Review
    assert decision.route == RouteDecision.HUMAN_REVIEW
    assert decision.approval_token is None


def test_auto_approve_clean_case():
    """
    Case with p_wrong <= 0.05 and rules satisfied auto-approves and generates approval token.
    """
    engine = DecisionEngine()
    scores = ComponentScores(
        identity=0.98,
        ocr=0.96,
        authenticity=0.97,
        rules_complete=0.98,
        scam_safety=0.99
    )
    case_data = {"monthly_income": 22000.0, "requested_amount": 12000.0, "household_size": 4}
    decision = engine.evaluate_case("cas_test_2", case_data, scores)

    assert decision.confidence == 0.96
    assert decision.route == RouteDecision.AUTO_APPROVE
    assert decision.approval_token is not None
    assert len(decision.approval_token) >= 32


def test_ask_more_proof_when_blurry_document():
    """
    Case with borderline confidence or missing documents asks for proof.
    """
    engine = DecisionEngine()
    scores = ComponentScores(
        identity=0.88,
        ocr=0.72,  # Moderate OCR clarity
        authenticity=0.85,
        rules_complete=0.90,
        scam_safety=0.95
    )
    case_data = {"monthly_income": 22000.0, "requested_amount": 12000.0, "household_size": 4}
    missing = ["Utility bill photo"]
    decision = engine.evaluate_case("cas_test_3", case_data, scores, missing_docs=missing)

    assert decision.route == RouteDecision.ASK_MORE_PROOF
    assert "Utility bill photo" in decision.missing
    assert "Utility bill photo" in decision.reason_simple.en
    assert decision.approval_token is None


def test_system_never_auto_rejects():
    """
    CRITICAL RULE: The system NEVER auto-rejects.
    Even completely ineligible cases route to a Human Officer with handoff notes.
    """
    engine = DecisionEngine()
    scores = ComponentScores(
        identity=0.40,
        ocr=0.30,
        authenticity=0.20,
        rules_complete=0.10,
        scam_safety=0.50
    )
    case_data = {"monthly_income": 90000.0, "requested_amount": 50000.0, "household_size": 1}
    decision = engine.evaluate_case("cas_test_4", case_data, scores)

    # Route must be human_review, NOT a hard automated rejection
    assert decision.route == RouteDecision.HUMAN_REVIEW
    assert decision.route != "auto_reject"
