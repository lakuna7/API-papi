# Source Registry

This registry contains source families and external references that have passed user-agent discussion. Individual datasets still require their own live validation and source contract before implementation unless already validated below.

| Source / Family | Owner | Role | Status | Last live validation / review |
|---|---|---|---|---|
| FDA NDC Directory | U.S. FDA | Authoritative drug listing and NDC identity source | ADOPTED | 2026-09-27 |
| openFDA | U.S. FDA | Official API/bulk representation across NDC, Drugs@FDA, labels, FAERS, recalls, shortages, regulatory and other FDA datasets | ADOPTED SOURCE FAMILY | 2026-09-27 |
| FDA/openfda GitHub | U.S. FDA | Official technical/source-genealogy reference for pipelines, schemas, upstream sources and API behavior | ADOPTED TECHNICAL REFERENCE | 2026-09-27 |
| RxNav / RxNorm | U.S. National Library of Medicine | NDC↔RxCUI, concept hierarchy, terminology, RxClass enrichment and historical concept status | ADOPTED SOURCE FAMILY | 2026-09-27 |
| DailyMed | U.S. National Library of Medicine | SPL/label identity, packaging, SetID/version history and validation | ADOPTED | 2026-09-27 |
| CMS / Medicare pharma data | CMS | Part D formulary/access/utilization/spending and Part B payment-limit/ASP/HCPCS data families | ADOPTED DISCOVERY FAMILY | 2026-09-27 |
| Medicaid drug data | CMS / Medicaid.gov | NADAC, SDUD, MDRP product data, FUL and related public drug-pricing/utilization datasets | ADOPTED DISCOVERY FAMILY | 2026-09-27 |
| fabkury/n2c | External open-source project | RxNorm querying/caching implementation reference; MIT licensed | REFERENCE | 2026-09-27 |
| Augmented-Nature/OpenFDA-MCP-Server | External open-source project | UX/query-pattern reference only; underlying FDA sources must be validated directly | REFERENCE ONLY | 2026-09-27 |
| EndurantDevs/healthcare-mrf-api | External open-source project | Discovery signpost for public healthcare-data families; do not reuse code/processed outputs | DISCOVERY SIGNPOST | 2026-09-27 |

## Operating rule

Third-party repositories can reveal useful structures, joins, KPIs and source families. When they point to potentially valuable data, locate and validate the original raw/public source and record that upstream source as the evidence base.

Detailed source contracts are added as each source is investigated and its operational role is finalized.
