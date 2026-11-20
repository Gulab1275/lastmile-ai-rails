"""
Webhook Dispatch and Events Management.
Allows external government or relief partner systems to subscribe to case lifecycle events.
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, status

from services.api.security.rbac import require_admin
from services.shared.schemas import UserResponse, WebhookEvent, WebhookSubscription

router = APIRouter(prefix="/webhooks", tags=["Webhooks & Integrations"])

_WEBHOOK_SUBS: Dict[str, WebhookSubscription] = {}
_DELIVERIES: List[WebhookEvent] = []


@router.post("/subscribe", response_model=WebhookSubscription, status_code=status.HTTP_201_CREATED)
async def subscribe_webhook(
    sub_in: dict,
    current_user: UserResponse = Depends(require_admin)
):
    """Subscribes an external endpoint to system events."""
    sub_id = f"wh_{uuid.uuid4().hex[:10]}"
    secret = f"whsec_{uuid.uuid4().hex[:20]}"
    sub = WebhookSubscription(
        id=sub_id,
        target_url=sub_in.get("target_url", "https://example.com/webhook"),
        event_types=sub_in.get("event_types", ["case.approved", "case.rejected"]),
        is_active=True,
        secret=secret,
        created_at=datetime.utcnow()
    )
    _WEBHOOK_SUBS[sub_id] = sub
    return sub


@router.get("/deliveries", response_model=List[WebhookEvent])
async def list_deliveries(
    current_user: UserResponse = Depends(require_admin)
):
    """Inspects recent webhook deliveries."""
    return _DELIVERIES[-50:]


def trigger_webhook_event(event_type: str, payload: Dict[str, Any]):
    """Internal helper to dispatch event to active subscriptions."""
    ev = WebhookEvent(
        event_id=f"evt_{uuid.uuid4().hex[:12]}",
        event_type=event_type,
        timestamp=datetime.utcnow(),
        payload=payload
    )
    _DELIVERIES.append(ev)
