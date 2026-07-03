"""Personalized email copy generation via the Anthropic (Claude) API.

The compliance footer (legal basis + working unsubscribe link) is appended in code, after
generation, rather than left to the model - so an unsubscribe link can never be missing or
malformed because of how the model responded.
"""
from __future__ import annotations

from dataclasses import dataclass

import anthropic

from app.core.config import get_settings
from app.core.security import build_unsubscribe_url
from app.models.campaign import Campaign
from app.models.email_message import MessageType
from app.models.lead import Lead


@dataclass
class EmailContent:
    subject: str
    body: str


_SYSTEM_PROMPT = (
    "Sei un copywriter B2B che scrive email di primo contatto commerciale in italiano, per "
    "conto dell'azienda del mittente. Scrivi in modo diretto, professionale, breve (massimo "
    "120 parole), senza formule di saluto eccessive, senza markdown. Non includere link di "
    "disiscrizione, firme legali o note di compliance: vengono aggiunti automaticamente dopo "
    "il tuo testo. Rispondi SOLO nel formato:\nOGGETTO: <oggetto email>\n\n<corpo email>"
)


def _build_user_prompt(campaign: Campaign, lead: Lead, message_type: MessageType) -> str:
    contact_name = " ".join(filter(None, [lead.contact_first_name, lead.contact_last_name])) or "il destinatario"
    lines = [
        f"Tono di voce richiesto: {campaign.email_tone_of_voice or 'professionale, diretto, non aggressivo'}",
        f"Destinatario: {contact_name}, ruolo: {lead.role_title or 'non specificato'}",
        f"Azienda destinataria: {lead.company_name}, settore: {lead.industry or 'non specificato'}",
    ]
    if message_type == MessageType.FIRST:
        lines.append(
            "Scrivi la prima email di contatto: presenta brevemente il valore per il "
            "destinatario, individua un pain point plausibile per il suo settore, e proponi "
            "una breve call conoscitiva. Non menzionare prezzi."
        )
    else:
        lines.append(
            "Scrivi un'email di follow-up perche' non hai ricevuto risposta alla prima email. "
            f"Proponi questa offerta specifica: {campaign.followup_offer_text or 'una call conoscitiva gratuita'}. "
            "Sii breve e non ripetere gli stessi argomenti del primo contatto."
        )
    return "\n".join(lines)


def _compliance_footer(lead: Lead) -> str:
    unsubscribe_url = build_unsubscribe_url(lead.id)
    return (
        "---\n"
        "Hai ricevuto questa email in quanto contatto professionale ritenuto potenzialmente "
        "interessato, ai sensi dell'art. 6.1.f GDPR (legittimo interesse B2B).\n"
        f"Per non ricevere piu' comunicazioni: {unsubscribe_url}"
    )


def generate_email(campaign: Campaign, lead: Lead, message_type: MessageType) -> EmailContent:
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY is not configured")

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=600,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _build_user_prompt(campaign, lead, message_type)}],
    )
    raw = "".join(block.text for block in response.content if block.type == "text").strip()

    subject, _, body = raw.partition("\n\n")
    subject = subject.removeprefix("OGGETTO:").strip() or f"Contatto {lead.company_name}"
    body = body.strip() or raw

    return EmailContent(subject=subject, body=f"{body}\n\n{_compliance_footer(lead)}")
