"""Pluggable lead-sourcing interface.

Every source (Apollo.io, and future ones like Registro Imprese or Google
Custom Search) implements `LeadSource.search(icp)` and returns a list of
`SourcedLead` records. The sourcing service (Phase 2) dedupes the results
against the `leads` table and the `suppressions` table before persisting.

Implemented in Phase 2.
"""
