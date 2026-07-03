from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.email_message import MessageStatus, MessageType


class EmailMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lead_id: int
    campaign_id: int
    message_type: MessageType
    subject: str
    body: str
    status: MessageStatus
    dry_run: bool
    graph_message_id: str | None
    graph_conversation_id: str | None
    sent_at: datetime | None
    error_detail: str | None
