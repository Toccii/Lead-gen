"""Pluggable lead-sourcing interface.

Every source (Apollo.io, and future ones like Registro Imprese or Google
Custom Search) implements `LeadSource.search(criteria, limit)` and returns a
list of `SourcedLead`. The sourcing service (app/sourcing/service.py) dedupes
the results against the `leads` table and the `suppressions` table before
persisting.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ICPCriteria:
    """Search criteria derived from a campaign's ICP config."""

    industries: list[str] = field(default_factory=list)
    geography: list[str] = field(default_factory=list)
    target_roles: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    company_size_min: int | None = None
    company_size_max: int | None = None


@dataclass
class SourcedLead:
    """Normalized result returned by a LeadSource, before dedup/persistence."""

    company_name: str
    contact_first_name: str | None = None
    contact_last_name: str | None = None
    role_title: str | None = None
    email: str | None = None
    website: str | None = None
    linkedin_company_url: str | None = None
    industry: str | None = None
    company_size: int | None = None
    source_id: str | None = None


class LeadSource(ABC):
    name: str

    @abstractmethod
    def search(self, criteria: ICPCriteria, limit: int) -> list[SourcedLead]:
        ...
