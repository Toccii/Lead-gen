"""Sends mail via Microsoft Graph API using application permissions (client-credentials flow,
no interactive user - required since cron jobs run unattended).

Uses the create-draft-then-send pattern (POST /messages, then POST /messages/{id}/send)
instead of the single-call /sendMail, because sendMail returns no body and we need an id to
correlate replies in Phase 4. Note: Graph may assign the sent message a *different* id once it
moves from Drafts to Sent Items, so `graph_conversation_id` - which stays stable across the
whole thread - is the reliable key for reply matching, not `graph_message_id`.
"""
from __future__ import annotations

from dataclasses import dataclass

import httpx
import msal

from app.core.config import get_settings

GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
GRAPH_SCOPE = ["https://graph.microsoft.com/.default"]


class GraphAuthError(RuntimeError):
    pass


@dataclass
class SentMessage:
    graph_message_id: str
    graph_conversation_id: str | None


def get_access_token() -> str:
    settings = get_settings()
    if not (settings.ms_graph_tenant_id and settings.ms_graph_client_id and settings.ms_graph_client_secret):
        raise GraphAuthError("Microsoft Graph credentials are not configured")

    confidential_app = msal.ConfidentialClientApplication(
        client_id=settings.ms_graph_client_id,
        client_credential=settings.ms_graph_client_secret,
        authority=f"https://login.microsoftonline.com/{settings.ms_graph_tenant_id}",
    )
    result = confidential_app.acquire_token_for_client(scopes=GRAPH_SCOPE)
    if "access_token" not in result:
        raise GraphAuthError(result.get("error_description", "failed to acquire Graph access token"))
    return result["access_token"]


def send_email(to_address: str, subject: str, body_text: str) -> SentMessage:
    settings = get_settings()
    mailbox = settings.ms_graph_sender_mailbox
    if not mailbox:
        raise GraphAuthError("MS_GRAPH_SENDER_MAILBOX is not configured")

    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    draft_payload = {
        "subject": subject,
        "body": {"contentType": "Text", "content": body_text},
        "toRecipients": [{"emailAddress": {"address": to_address}}],
    }

    with httpx.Client(timeout=30.0) as client:
        draft_resp = client.post(
            f"{GRAPH_BASE_URL}/users/{mailbox}/messages", json=draft_payload, headers=headers
        )
        draft_resp.raise_for_status()
        draft = draft_resp.json()
        message_id = draft["id"]
        conversation_id = draft.get("conversationId")

        send_resp = client.post(
            f"{GRAPH_BASE_URL}/users/{mailbox}/messages/{message_id}/send", headers=headers
        )
        send_resp.raise_for_status()

    return SentMessage(graph_message_id=message_id, graph_conversation_id=conversation_id)
