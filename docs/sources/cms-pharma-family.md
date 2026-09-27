# CMS / Medicaid Pharmaceutical Source Family

Status: ADOPTED AS DISCOVERY FAMILY
Owners: Centers for Medicare & Medicaid Services / Medicaid.gov
Last reviewed: 2026-09-27

Individual datasets require live validation and source contracts before implementation.

## Medicare Part D — market access / formulary

### Monthly Prescription Drug Plan Formulary and Pharmacy Network Information
Potential roles:
- plan and contract attributes;
- formulary coverage by NDC;
- tier;
- prior authorization;
- step therapy;
- quantity limits;
- indication-based coverage where supplied;
- pharmacy network and pharmacy NPI;
- beneficiary cost-sharing-related plan data.

Native time context: monthly snapshot/release.

### Quarterly Prescription Drug Plan Formulary, Pharmacy Network, and Pricing Information
Includes similar plan/formulary/network information and additionally provides plan-level average monthly unit costs for formulary Part D drugs.

Native time context: quarterly.

Important: monthly and quarterly products are not interchangeable merely because they overlap.

### Formulary Reference File
Official CMS reference files for the Part D formulary environment. Investigate as a reference/crosswalk source rather than assuming it has plan-level coverage.

### MA / Part D contract and enrollment data
Monthly plan/contract enrollment data can potentially provide plan-size weights for access/formulary analysis.

## Medicare Part D — utilization / spending

Candidate official datasets:
- Part D Prescribers by Provider and Drug;
- Part D Prescribers by Geography and Drug;
- Part D Prescribers by Provider;
- Medicare Part D Spending by Drug.

Potential outputs:
- fills/prescriptions;
- drug cost;
- prescriber/provider NPI relationships;
- geography;
- beneficiary/spending metrics where published.

These datasets have their own aggregation and suppression rules and must not be projected to NDC/package grain without an explicit method.

## Medicare Part B — drug pricing / reimbursement

### Medicare Part B Drug Payment Limit File
Quarterly public files containing payment limits for Part B drugs and biologicals.

Most separately payable drugs are associated with ASP-based methodologies, but current files can also contain other payment methodologies. The published payment limit should therefore be treated as the native CMS fact; do not blindly label every payment limit as ASP.

### NDC–HCPCS crosswalk
Quarterly public crosswalk associated with the Part B payment-limit files.

This is a key official bridge between package/product NDCs and HCPCS billing codes.

### HCPCS quarterly files
Official quarterly HCPCS code-system updates. Useful for HCPCS identity/description/status context.

## Medicaid — product / reimbursement / utilization

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
State-reported utilization for covered outpatient drugs.

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
Quarterly product snapshots plus weekly newly reported active covered outpatient drug files.

Important fields can include:
- NDC segments;
- labeler;
- product/FDA name;
- drug category/type;
- FDA application;
- market/coverage dates;
- unit type and package size;
- therapeutic-equivalence and other program indicators.

This is potentially valuable as an independent official product/coverage dimension and timing source.

### ACA Federal Upper Limits (FUL)
Official Medicaid drug-pricing/payment reference source based on applicable AMP-derived methodology for multiple-source drugs.

Investigate cadence, native identifier grain, and historical availability during its dedicated source cycle.

## Access

CMS and Medicaid sources may expose combinations of:
- API;
- CSV/ZIP bulk downloads;
- browser dataset explorer;
- manual downloads;
- reference files.

All viable access routes should be recorded, including reproducible manual extraction.

## Key rule

CMS/Medicaid datasets are a family, not one homogeneous source.

For each dataset we must separately establish:
- native identifier grain;
- native time grain;
- reporting lag;
- suppression;
- units;
- population covered;
- whether amounts are price, payment limit, acquisition cost, reimbursement, spending or another economic concept.
