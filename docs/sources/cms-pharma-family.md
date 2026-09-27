# CMS / Medicaid Pharmaceutical Source Family

Status: ADOPTED SOURCE FAMILY
Owners: Centers for Medicare & Medicaid Services / Medicaid.gov
Last reviewed: 2026-09-27

## Current validation state

Detailed live-validated CMS contracts now exist for:

- `cms-part-d.md` — Part D formulary/access, annual spending and preliminary quarterly-refreshed spending;
- `cms-part-b.md` — Part B annual/preliminary spending, quarterly payment limits, NDC-HCPCS crosswalks and HCPCS reference.

Medicaid sources remain a discovery family until each receives its dedicated live source contract.

## Medicare Part D

Adopted source roles:

- Monthly Prescription Drug Plan Formulary and Pharmacy Network Information — monthly formulary/access/network snapshot.
- Quarterly Prescription Drug Plan Formulary, Pharmacy Network, and Pricing Information — quarterly snapshot plus plan-level drug pricing.
- Medicare Part D Spending by Drug — annual drug/manufacturer program-summary spending and utilization.
- Medicare Quarterly Part D Spending by Drug — preliminary, periodically refreshed spending periods.
- Part D Prescriber datasets — provider/drug utilization dimension; dedicated validation later.

Important semantics:

- CMS formulary NDC is a proxy NDC associated with the drug product, not evidence of an exact dispensed package.
- RxCUI is an important semantic bridge between Part D formulary data and the project's RxNorm layer.
- update frequency, represented reporting period, contract year and publication date are different concepts.
- the preliminary spending product may contain cumulative labels such as `2025 (Q1-Q4)`; do not model it as one independent calendar-quarter fact simply because the product is refreshed quarterly.

## Medicare Part B

Adopted source roles:

- Medicare Part B Spending by Drug — annual HCPCS-native spending/utilization.
- Medicare Quarterly Part B Spending by Drug — preliminary, periodically refreshed HCPCS-native spending/utilization.
- Medicare Part B Drug Payment Limit Files — quarterly payment facts.
- CMS NDC-HCPCS Crosswalk — official package-NDC to HCPCS billing-code bridge.
- Quarterly HCPCS code files — billing-code identity/reference context.

Important semantics:

- HCPCS is the native billing identifier for Part B facts.
- NDC-to-HCPCS mapping should use the official quarterly CMS crosswalk rather than brand-name inference.
- the current CMS crosswalk publication can contain distinct ASP, AWP, OPPS and PrEP crosswalk files; preserve payment context.
- package quantity, HCPCS dosage and billing units are separate unit concepts.
- presence or absence in a Part B payment-limit/crosswalk file is not a Medicare coverage determination.

## Medicaid

### NADAC

National Average Drug Acquisition Cost reference data.

Native characteristics:
- NDC;
- NADAC per unit;
- pricing unit;
- effective date;
- weekly reference data.

Potential roles:
- acquisition-cost benchmark;
- price trend;
- WAC/NADAC comparison where WAC is available;
- reimbursement/economic analyses.

### State Drug Utilization Data (SDUD)

State-reported covered-outpatient-drug utilization.

Native characteristics include:
- state;
- utilization type (FFS/MCO);
- NDC;
- year and quarter;
- units reimbursed;
- prescriptions;
- reimbursement amounts;
- suppression indicator.

Potential roles:
- Medicaid utilization;
- state share;
- FFS/MCO mix;
- reimbursed amount per unit/prescription;
- longitudinal utilization/spend.

### Medicaid Drug Rebate Program product data

Quarterly product snapshots plus weekly newly reported active covered-outpatient-drug files.

Potentially important fields include:
- NDC segments;
- labeler;
- product/FDA name;
- drug category/type;
- FDA application;
- market/coverage dates;
- unit type and package size;
- therapeutic-equivalence and program indicators.

### ACA Federal Upper Limits

Official Medicaid drug pricing/payment reference source for applicable multiple-source drugs.

Dedicated validation still required.

## Access

CMS and Medicaid sources may expose combinations of:
- API;
- CSV/ZIP bulk downloads;
- browser dataset explorer;
- manual downloads;
- reference files.

All viable public access routes should be retained, including reproducible manual extraction.

## Key rule

CMS/Medicaid is a source family, not a homogeneous dataset.

For every source preserve:
- identifier grain;
- represented time period;
- release/update cadence;
- reporting lag and maturity;
- suppression;
- units;
- covered population;
- economic meaning: acquisition cost, reimbursement, spending, payment limit, plan cost or another concept.
