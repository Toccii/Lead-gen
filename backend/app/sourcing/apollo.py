"""Apollo.io People Search adapter.

Requires `APOLLO_API_KEY`. Apollo's public API surface (endpoint paths, field names, and
whether an email is included directly in search results vs. requiring a separate paid
enrichment call) changes over time and depends on the plan/credits available on the account.
This implementation follows Apollo's documented People Search endpoint as of writing
(https://docs.apollo.io/reference/people-search) but has not been exercised against a live
account. Verify field names and response shape against the current docs once a real API key is
available, before relying on it for a real send.
"""
from __future__ import annotations

import httpx

from app.core.config import get_settings
from app.sourcing.base import ICPCriteria, LeadSource, SourcedLead

APOLLO_SEARCH_URL = "https://api.apollo.io/api/v1/mixed_people/search"


class ApolloLeadSource(LeadSource):
    name = "apollo"

    def __init__(self, api_key: str | None = None) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.apollo_api_key
        if not self.api_key:
            raise ValueError("APOLLO_API_KEY is not configured")

    def search(self, criteria: ICPCriteria, limit: int) -> list[SourcedLead]:
        payload: dict = {
            "page": 1,
            "per_page": min(limit, 100),
        }
        if criteria.target_roles:
            payload["person_titles"] = criteria.target_roles
        if criteria.keywords:
            payload["q_keywords"] = " ".join(criteria.keywords)
        if criteria.geography:
            payload["person_locations"] = criteria.geography
        if criteria.industries:
            payload["q_organization_keyword_tags"] = criteria.industries
        if criteria.company_size_min or criteria.company_size_max:
            lo = criteria.company_size_min or 1
            hi = criteria.company_size_max or 100000
            payload["organization_num_employees_ranges"] = [f"{lo},{hi}"]

        headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "x-api-key": self.api_key,
        }

        with httpx.Client(timeout=30.0) as client:
            response = client.post(APOLLO_SEARCH_URL, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        leads: list[SourcedLead] = []
        for person in data.get("people", [])[:limit]:
            organization = person.get("organization") or {}
            company_name = organization.get("name")
            if not company_name:
                continue
            leads.append(
                SourcedLead(
                    company_name=company_name,
                    contact_first_name=person.get("first_name"),
                    contact_last_name=person.get("last_name"),
                    role_title=person.get("title"),
                    email=person.get("email"),
                    website=organization.get("website_url"),
                    linkedin_company_url=organization.get("linkedin_url"),
                    industry=organization.get("industry"),
                    company_size=organization.get("estimated_num_employees"),
                    source_id=person.get("id"),
                )
            )
        return leads
