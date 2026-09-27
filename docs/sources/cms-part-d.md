# CMS Medicare Part D Source Contract

Status: ADOPTED
Owner: Centers for Medicare & Medicaid Services (CMS)
Last live validation: 2026-09-27

## Role

CMS Part D is not one dataset. The project will preserve separate source roles for:

1. formulary / access / plan / pharmacy-network information;
2. drug spending and utilization summaries;
3. prescriber/provider utilization datasets where useful.

These sources remain at their native grain and are not forced to package-NDC grain.

---

## 1. Monthly Prescription Drug Plan Formulary and Pharmacy Network Information

Official landing page:
https://data.cms.gov/provider-summary-by-type-of-service/medicare-part-d-prescribers/monthly-prescription-drug-plan-formulary-and-pharmacy-network-information

Access modes:
- BULK — official ZIP;
- MANUAL — landing-page download;
- DISCOVERY — CMS catalog/JSON metadata can be used to resolve the current file dynamically.

Update cadence: Monthly.

Live state on 2026-09-27:
- latest available release: September 2026;
- page last modified: 2026-09-23;
- current ZIP filename: `2026_20260916.zip`;
- ZIP size: 2,291,903,716 bytes;
- MD5 published by CMS metadata: `4c43b28938907fdb10f35a8ad11be189`.

The current file URL was resolved from CMS metadata rather than assumed from a hardcoded version URL.

### Discovery method

Prefer discovery from the stable dataset title/landing page and CMS catalog metadata, including:
- https://data.cms.gov/data.json
- the data.cms.gov dataset JSONAPI relationships.

Version-specific CMS file UUIDs and ZIP URLs may be retained as retrieval evidence/cache hints but should not be treated as permanent identifiers.

### Native file structure

The 2026 monthly PUF methodology defines eight separate flat ASCII, pipe-delimited files with headers.

The source includes:
- Plan Information;
- Geographic Locator;
- Basic Drugs Formulary;
- Excluded Drugs Formulary;
- Beneficiary Cost;
- Pharmacy Network;
- Indication Based Coverage Formulary;
- Insulin Beneficiary Cost.

Official 2026 record layout:
https://data.cms.gov/sites/default/files/2025-10/0564eb37-402d-4110-bd98-2d5399dc30e7/PUFRecordLayout-2026.pdf

Official 2026 methodology:
https://data.cms.gov/sites/default/files/2025-10/8f1d8b42-bfd1-4f9c-b86d-b92af0c6f3d5/Methodology-PUF-2026.pdf

### Basic Drugs Formulary fields

The 2026 record layout defines:
- `FORMULARY_ID`;
- `FORMULARY_VERSION`;
- `CONTRACT_YEAR`;
- `RXCUI`;
- `NDC` — 11-digit **proxy NDC** associated with the drug product;
- `TIER_LEVEL_VALUE`;
- `QUANTITY_LIMIT_YN`;
- `QUANTITY_LIMIT_AMOUNT`;
- `QUANTITY_LIMIT_DAYS`;
- `PRIOR_AUTHORIZATION_YN`;
- `STEP_THERAPY_YN`;
- `SELECTED_DRUG_YN` — 2026 flag for a Part D drug selected for negotiation.

The proxy NDC is not evidence that the exact physical package was dispensed or that coverage is uniquely package-specific. RxCUI is a key semantic bridge to the project's RxNorm layer.

Do not assume a unique row key beyond the fields documented by CMS until duplicate behavior is tested on the extracted release.

### Plan grain

CMS states that a plan is uniquely identified by:

```text
CONTRACT_ID + PLAN_ID + SEGMENT_ID
```

Plan Information links plans to `FORMULARY_ID`.

Important plan fields include:
- contract/plan/segment;
- plan and contract names;
- formulary ID;
- premium;
- deductible;
- plan geography/type;
- SNP indicator;
- `PLAN_SUPPRESSED_YN`.

Suppressed plans appear in Plan Information but not the other PUF files.

### Indication-based coverage

The file contains:
- `CONTRACT_ID`;
- `PLAN_ID`;
- `RXCUI`;
- `DISEASE` — FDA-approved indication for which the RxCUI is considered on-formulary.

This should be treated as CMS plan/formulary indication-based coverage information, not as a replacement for FDA-approved labeling.

### Beneficiary cost

The beneficiary-cost table is plan/segment/tier/days-supply oriented and includes preferred, non-preferred and mail-order cost sharing, specialty-tier indicators and deductible applicability.

### Pharmacy network

The pharmacy-network file relates plan/segment to pharmacy identifiers and network attributes, including:
- pharmacy number derived from NPI;
- ZIP;
- preferred retail/mail indicators;
- network status;
- in-area flag;
- floor price;
- dispensing fees by days supply and drug category.

This creates a future bridge:

```text
drug/RxCUI → formulary → plan → pharmacy/NPI → geography
```

### Contract-year timing

Benefit-year data becomes available before the benefit year begins.

Example documented by CMS:
- 2026 contract-year data appears in October-December 2025 files and January-September 2026 files;
- beginning with the October 2026 monthly release, the file moves to contract year 2027.

Therefore:
- file release month;
- contract year;
- source publication date

must remain separate concepts.

### Limitations

- employer-sponsored plans and national PACE plans are excluded; the methodology also identifies other excluded plan categories;
- plan data may be suppressed;
- files are large;
- the PUF is a snapshot of the first new Medicare Plan Finder posting for the month;
- Medicare Plan Finder may update more frequently than the PUF;
- the proxy NDC must not be interpreted as a dispensing record or exact package-use fact.

---

## 2. Quarterly Prescription Drug Plan Formulary, Pharmacy Network, and Pricing Information

Official landing page:
https://data.cms.gov/provider-summary-by-type-of-service/medicare-part-d-prescribers/quarterly-prescription-drug-plan-formulary-pharmacy-network-and-pricing-information

Status: ADOPTED

Update cadence: Quarterly.

Live state on 2026-09-27:
- latest available: Q2 2026;
- next scheduled release shown by CMS: 2026-10-15.

The quarterly SPUF contains the same major access/network concepts plus a **Pricing** file unavailable in the monthly PUF.

Official 2026 record layout:
https://data.cms.gov/sites/default/files/2025-10/83da019f-fa24-483e-87de-cc089780a6a5/SPUFRecordLayout-2026.pdf

Official 2026 methodology:
https://data.cms.gov/sites/default/files/2025-10/cf6b8476-ca42-48c6-9fc4-281b08c6ea87/Methodology-SPUF-2026.pdf

The 2026 SPUF methodology defines nine flat ASCII, pipe-delimited files with headers.

### Pricing fields

The quarterly pricing table includes:
- `CONTRACT_ID`;
- `PLAN_ID`;
- `SEGMENT_ID`;
- `NDC` — 11-digit proxy NDC;
- `DAYS_SUPPLY`;
- `UNIT_COST` — average unit cost for the specified days supply at in-area retail pharmacies.

Monthly and quarterly PUFs therefore serve different purposes:
- monthly = fresher access/formulary/network snapshot;
- quarterly = less frequent snapshot plus pricing information.

Do not treat them as interchangeable releases.

---

## 3. Medicare Part D Spending by Drug — Annual

Official dataset:
https://data.cms.gov/summary-statistics-on-use-and-payments/medicare-medicaid-spending-by-drug/medicare-part-d-spending-by-drug

CMS Data API dataset ID:
`7e0b4365-fd63-4a29-8f5e-e0ac9f66a81b`

API:
https://data.cms.gov/data-api/v1/dataset/7e0b4365-fd63-4a29-8f5e-e0ac9f66a81b/data

Access mode: API + CMS bulk/data portal.

Live API validation on 2026-09-27 succeeded.

Current annual release exposes 2020-2024 measures including:
- `Brnd_Name`;
- `Gnrc_Name`;
- `Tot_Mftr`;
- `Mftr_Name`;
- total spending by year;
- total dosage units by year;
- total claims by year;
- total beneficiaries by year;
- weighted average spending per dosage unit;
- average spending per claim;
- average spending per beneficiary;
- outlier flags;
- change/CAGR fields.

Native identity is drug/manufacturer naming, not NDC package identity.

Spending is a program-summary economic fact and must not be projected to an individual NDC package as if it were package-native.

---

## 4. Medicare Quarterly Part D Spending by Drug

Official dataset:
https://data.cms.gov/summary-statistics-on-use-and-payments/medicare-medicaid-spending-by-drug/medicare-quarterly-part-d-spending-by-drug

CMS Data API dataset ID:
`4ff7c618-4e40-483a-b390-c8a58c94fa15`

API:
https://data.cms.gov/data-api/v1/dataset/4ff7c618-4e40-483a-b390-c8a58c94fa15/data

Access mode: API + CMS data portal.

Live API validation on 2026-09-27 succeeded.

A current record used a period label such as:

```text
Year = "2025 (Q1-Q4)"
```

This is a critical temporal semantic.

The dataset is **refreshed quarterly but is not necessarily a one-calendar-quarter fact table**. It represents preliminary/maturing spending periods that can accumulate through Q1, Q1-Q2, Q1-Q3 or Q1-Q4 and are later superseded by the annual product.

Important fields observed live include:
- `Brnd_Name`;
- `Gnrc_Name`;
- `Tot_Mftr`;
- `Mftr_Name`;
- `Year` reporting-period label;
- `Tot_Benes`;
- `Tot_Clms`;
- `Tot_Spndng`;
- spending averages;
- `Drug_Uses`.

For this source, keep separate:
- update cadence;
- represented reporting period;
- data-through period;
- publication/retrieval date;
- preliminary/final maturity status.

---

## 5. Part D Prescriber datasets

CMS Part D Prescriber datasets remain in scope as a provider/utilization dimension.

The important conceptual grain is provider/prescriber plus drug identity, not package NDC.

Potential relationship:

```text
NPI → brand/generic drug concept → claims/cost/utilization
```

Do not reject a useful source merely because it cannot be reduced to NDC-11. A dedicated live source contract will be completed when the provider dimension is investigated.

---

## Useful outputs / KPIs

Potential future outputs include:
- formulary coverage breadth;
- lives-weighted formulary coverage after enrollment is joined;
- tier distribution;
- PA/ST/QL prevalence;
- selected-drug coverage;
- indication-based coverage;
- beneficiary cost-sharing comparisons;
- pharmacy-network breadth;
- preferred-network share;
- plan-level quarterly drug unit-cost comparisons;
- annual and preliminary Part D spending/utilization trends;
- prescriber concentration and geography after dedicated validation.

Each output must retain the native source grain and population.

## Core semantic rule

```text
FORMULARY PROXY NDC ≠ DISPENSED PACKAGE NDC
PART D SPENDING DRUG ≠ PACKAGE NDC
UPDATE FREQUENCY ≠ NATIVE REPORTING PERIOD
```
