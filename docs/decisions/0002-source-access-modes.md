# ADR-0002 — Source Access Modes

Status: Accepted
Date: 2026-09-27

## Decision

A useful public source is not rejected merely because it lacks a clean automated API.

The project will explicitly record all viable public access paths, including workflows that require manual extraction by the user.

## Access modes

Each source may expose one or more of:

- API — machine-readable live endpoint.
- BULK — downloadable structured files such as CSV, XLSX, JSON, ZIP or XML.
- MANUAL — public data that requires browser interaction, filtering, export or another reproducible human step.
- HYBRID — an automated workflow that depends on a limited manual step, such as periodically downloading a public file or resolving a changing resource.
- LOCAL — an official locally installable distribution or service.
- MIRROR — an official or approved secondary distribution of the same underlying data.

Multiple access modes should be recorded when available.

## Manual-source requirements

For a manual or hybrid source, record:

- official page or portal;
- owner;
- exact manual steps;
- filters/selections required;
- export format;
- expected grain;
- update cadence;
- whether historical versions are available;
- whether extraction is reproducible;
- relevant terms/licensing;
- last successful manual validation date;
- what fields/outputs are uniquely available through the manual route.

Manual extraction should not be described as an API connection.

## Connection preference

Prefer, where equivalent:

API or structured bulk > official local service > reproducible manual/hybrid extraction > unstable scraping.

However, a manual source can still be ADOPTED when it provides important public information that is unavailable through a better machine-readable route.

## Principle

Access convenience and data value are separate dimensions. Preserve useful public sources even when the user must perform part of the retrieval manually.
