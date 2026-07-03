"""Reads the outreach mailbox via Microsoft Graph to detect replies (Module 4). Reuses the
app-only auth from app.email.sender - same mailbox, same credentials, read instead of write.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

from app.core.config import get_settings
from app.email.sender import GRAPH_BASE_URL, GraphAuthError, get_access_token


@dataclass
class InboundMessage:
    graph_message_id: str
    graph_conversation_id: str | None
    from_address: str | None
    received_at: datetime
    snippet: str | None


def _parse_graph_datetime(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def fetch_recent_inbox_messages(since: datetime) -> list[InboundMessage]:
    """Fetches inbox messages received on/after `since`, paging through all results."""
    settings = get_settings()
    mailbox = settings.ms_graph_sender_mailbox
    if not mailbox:
        raise GraphAuthError("MS_GRAPH_SENDER_MAILBOX is not configured")

    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    since_iso = since.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    url = f"{GRAPH_BASE_URL}/users/{mailbox}/mailFolders/inbox/messages"
    params: dict | None = {
        "$filter": f"receivedDateTime ge {since_iso}",
        "$select": "id,conversationId,from,receivedDateTime,bodyPreview",
        "$top": "100",
    }

    messages: list[InboundMessage] = []
    with httpx.Client(timeout=30.0) as client:
        while url:
            resp = client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("value", []):
                received_raw = item.get("receivedDateTime")
                messages.append(
                    InboundMessage(
                        graph_message_id=item["id"],
                        graph_conversation_id=item.get("conversationId"),
                        from_address=((item.get("from") or {}).get("emailAddress") or {}).get("address"),
                        received_at=(
                            _parse_graph_datetime(received_raw) if received_raw else datetime.now(timezone.utc)
                        ),
                        snippet=item.get("bodyPreview"),
                    )
                )
            url = data.get("@odata.nextLink")
            params = None  # nextLink already includes the query string
    return messages
