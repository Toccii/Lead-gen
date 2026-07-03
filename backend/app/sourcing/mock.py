"""Deterministic fake lead source, for testing the sourcing pipeline (dedup, persistence,
execution logging) without an Apollo API key. Same criteria + limit always produce the same
leads, which also makes it useful for exercising the dedup logic across repeated runs.
"""
from __future__ import annotations

import re

from app.sourcing.base import ICPCriteria, LeadSource, SourcedLead

_COMPANIES = [
    "Rossi Meccanica", "Bianchi Logistica", "Verdi Consulting", "Ferrari Impianti",
    "Colombo Digital", "Ricci Costruzioni", "Marino Software", "Greco Energia",
    "Bruno Trasporti", "Gallo Servizi", "Conti Manifattura", "De Luca Retail",
]
_FIRST_NAMES = [
    "Marco", "Giulia", "Luca", "Francesca", "Andrea",
    "Elena", "Davide", "Chiara", "Simone", "Valentina",
]
_LAST_NAMES = [
    "Rossi", "Bianchi", "Verdi", "Ferrari", "Colombo",
    "Ricci", "Marino", "Greco", "Bruno", "Gallo",
]


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


class MockLeadSource(LeadSource):
    name = "mock"

    def search(self, criteria: ICPCriteria, limit: int) -> list[SourcedLead]:
        roles = criteria.target_roles or ["Titolare"]
        industries = criteria.industries or ["Servizi"]

        leads: list[SourcedLead] = []
        for i in range(limit):
            company = _COMPANIES[i % len(_COMPANIES)]
            first = _FIRST_NAMES[i % len(_FIRST_NAMES)]
            last = _LAST_NAMES[(i + 3) % len(_LAST_NAMES)]
            domain = f"{_slug(company)}.it"
            leads.append(
                SourcedLead(
                    company_name=company,
                    contact_first_name=first,
                    contact_last_name=last,
                    role_title=roles[i % len(roles)],
                    email=f"{first}.{last}@{domain}".lower(),
                    website=f"https://www.{domain}",
                    linkedin_company_url=f"https://www.linkedin.com/company/{_slug(company)}",
                    industry=industries[i % len(industries)],
                    company_size=25 + (i * 7) % 200,
                    source_id=f"mock-{_slug(company)}-{i}",
                )
            )
        return leads
