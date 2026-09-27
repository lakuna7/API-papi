# openFDA Source Family

Status: ADOPTED AS SOURCE FAMILY
Owner: U.S. Food and Drug Administration
Last reviewed: 2026-09-27

## Role

openFDA is broader than the NDC API. It provides official FDA API and bulk-download access across multiple regulatory and drug-information domains.

The official FDA/openfda GitHub repository is also adopted as a technical/source-genealogy reference because it contains ingestion pipelines, schemas, upstream source locations, transformation logic and API implementation details.

## Important drug-related families

### Identity and product listing
- NDC Directory / drug NDC API
- NSDE
- UNII
- Substance / GSRS-derived data

### Regulatory
- Drugs@FDA
- submissions and application history exposed through Drugs@FDA
- Complete Response Letters
- historical FDA documents where useful

### Labeling
- drug label / SPL-derived API data
- DailyMed remains a complementary primary SPL/label source and history layer

### Safety and supply
- FAERS drug adverse events
- drug enforcement / recalls
- drug shortages

## Access

Potential access paths:
- REST API;
- server-side search/count aggregation;
- official bulk downloads;
- original upstream FDA files;
- official FDA/openfda source repository for schemas and ingestion genealogy.

Individual datasets must still be validated separately before implementation.

## Fast aggregation opportunity

openFDA supports server-side count/group queries for many endpoints. These can be useful for fast descriptive summaries without downloading an entire dataset.

Examples of potential outputs:
- report counts by seriousness/reaction/date;
- shortage counts by status;
- counts by sponsor/application attributes;
- recall counts by classification/status;
- distribution summaries for categorical fields.

Counts must preserve the meaning and limitations of the underlying dataset. For example, FAERS counts are spontaneous reports and must not be interpreted as incidence or causal risk.

## Architecture principle

For each openFDA dataset, preserve:

```text
original FDA source
    ↓
openFDA ingestion / transformation
    ↓
openFDA API or bulk representation
    ↓
project normalized fact
```

Where practical, record both the original upstream source and the openFDA representation.

## Repository reference

Official repository:
https://github.com/FDA/openfda

License observed: CC0 1.0.

The repository may be used to understand source genealogy, schemas and transformations and, where useful, provide legally reusable implementation material. Any reused component should still be reviewed for present-day correctness before adoption.
