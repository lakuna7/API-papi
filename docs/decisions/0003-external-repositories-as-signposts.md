# ADR-0003 — Third-Party Repositories as Discovery Signposts

Status: Accepted
Date: 2026-09-27

## Decision

Third-party repositories may be used to discover useful source families, architecture patterns, retrieval methods, joins, KPIs, and operational ideas.

They are not treated as evidence for the underlying healthcare or pharmaceutical facts when an original public source can be identified.

## Required process

When an external repository points to potentially useful data:

1. identify the claimed upstream source;
2. find the original public agency/provider dataset, API, file or documentation;
3. validate the original source directly;
4. inspect its real grain, schema, identifiers, cadence and limitations;
5. record the original source, not the third-party interpretation, as the project data source.

Third-party claims about fields, cadence, availability, definitions, coverage or API behavior must be independently verified.

## Code reuse

Repository licensing must be checked before any code reuse.

A repository may be:

- REUSABLE — license permits the intended reuse;
- REFERENCE ONLY — architecture/query ideas may be studied but code should not be copied;
- DISCOVERY SIGNPOST — useful primarily because it reveals public upstream sources or system structure;
- REJECTED — unsuitable, misleading, obsolete, or incompatible.

Restrictive or unclear licensing means no code copying or adaptation unless permission is obtained.

## Data principle

Prefer the raw/official upstream source whenever available.

A useful structure discovered elsewhere may inspire an independently designed implementation, but the project should preserve independent source validation and provenance.

## Current examples

- FDA/openfda: official FDA repository; adopted as an official technical/source-genealogy reference.
- Augmented-Nature/OpenFDA-MCP-Server: reference for query/UX ideas only; do not reuse code.
- EndurantDevs/healthcare-mrf-api: discovery signpost only; do not reuse code or processed outputs. Investigate useful underlying public datasets independently.
