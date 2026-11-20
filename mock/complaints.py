"""
Mock Grievance & Citizen Complaints Service.
Simulates Citizen Redressal Portal for public welfare claims.
"""
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from mock.chaos import apply_chaos
from services.shared.schemas import MockComplaintRequest, MockComplaintResponse

_COMPLAINTS_STORE: Dict[str, Dict[str, Any]] = {}


async def lodge_complaint(
    req: MockComplaintRequest,
    chaos_mode: Optional[str] = None
) -> MockComplaintResponse:
    """
    Lodges a citizen grievance/complaint with queue routing.
    """
    await apply_chaos(chaos_mode)

    ticket_id = f"CMP-{datetime.utcnow().strftime('%y%m')}-{uuid.uuid4().hex[:6].upper()}"

    queue_mapping = {
        "scam_report": "CYBER_CRIME_TRIAGE",
        "delay": "DISTRICT_OFFICER_QUEUE",
        "wrong_deduction": "AUDIT_RECONCILIATION",
        "agent_misbehavior": "HELPER_OVERSIGHT"
    }

    assigned_queue = queue_mapping.get(req.category.lower(), "GENERAL_CITIZEN_PORTAL")

    resp = MockComplaintResponse(
        ticket_id=ticket_id,
        citizen_cnic=req.citizen_cnic,
        status="LOGGED",
        assigned_queue=assigned_queue,
        expected_resolution_days=3 if req.category == "scam_report" else 5,
        created_at=datetime.utcnow()
    )

    _COMPLAINTS_STORE[ticket_id] = {
        "ticket": resp.model_dump(),
        "phone": req.phone,
        "category": req.category,
        "description": req.description
    }

    return resp
