# CMS Medicare Part B Drug Source Contract

Status: ADOPTED
Owner: Centers for Medicare & Medicaid Services (CMS)
Last live validation: 2026-09-27

## Role

The Part B environment contains several distinct facts and identifier systems:

```text
NDC package
   ↓
official NDC ↔ HCPCS crosswalk
   ↓
HCPCS billing code
   ├── quarterly payment limit
   ├── annual spending/utilization
   └── preliminary spending/utilization
```

The NDC-HCPCS relationship is an official bridge. HCPCS remains the native billing identity for Part B spending/payment-limit facts.

---

## 1. Medicare Part B Spending by Drug — Annual

Official dataset:
https://data.cms.gov/summary-statistics-on-use-and-payments/medicare-medicaid-spending-by-drug/medicare-part-b-spending-by-drug

CMS Data API dataset ID:
`76a714ad-3a2c-43ac-b76d-9dadf8f7d890`

API:
https://data.cms.gov/data-api/v1/dataset/76a714ad-3a2c-43ac-b76d-9dadf8f7d890/data

Access mode: API + CMS data portal.

Live API validation on 2026-09-27 succeeded.

Current live fields include:
- `HCPCS_Cd`;
- `HCPCS_Desc`;
- `Brnd_Name`;
- `Gnrc_Name`;
- annual total spending;
- annual dosage units;
- annual claims;
- annual beneficiaries;
- average spending per dosage unit;
- average spending per claim;
- average spending per beneficiary;
- outlier flags;
- `Avg_DY24_ASP_Price` in the current vintage;
- change/CAGR fields.

Current annual measures extend through 2024.

Native identifier/grain is HCPCS-oriented, not NDC package grain.

The brand/generic fields are useful but HCPCS remains the primary technical identifier for the Part B fact.

CMS documentation distinguishes:
- ordinary brand/generic names;
- an asterisk when multiple names map to a HCPCS code;
- fallback to the HCPCS short description when a name is unavailable.

Do not discard the name fields, but do not use them as the primary bridge to package identity when the official NDC-HCPCS crosswalk is available.

---

## 2. Medicare Quarterly Part B Spending by Drug

Official dataset:
https://data.cms.gov/summary-statistics-on-use-and-payments/medicare-medicaid-spending-by-drug/medicare-quarterly-part-b-spending-by-drug

CMS Data API dataset ID:
`bf6a5b3b-31ee-4abb-b1ad-2607a1e7510a`

API:
https://data.cms.gov/data-api/v1/dataset/bf6a5b3b-31ee-4abb-b1ad-2607a1e7510a/data

Access mode: API + CMS data portal.

Live API validation on 2026-09-27 succeeded.

A current live record used:

```text
Year = "2025 (Q1-Q4)"
```

Therefore the source is quarterly-refreshed preliminary data, not necessarily a fact table with one independent row for each calendar quarter.

Observed fields include:
- `HCPCS_Cd`;
- `HCPCS_Desc`;
- `Brnd_Name`;
- `Gnrc_Name`;
- reporting-period label;
- total beneficiaries;
- total claims;
- total spending;
- average spending per beneficiary;
- average spending per claim.

Preserve update cadence, represented period and maturity/finality separately.

---

## 3. Medicare Part B Drug Payment Limit Files

Official source hub:
https://www.cms.gov/medicare/payment/part-b-drugs/asp-pricing-files

Status: ADOPTED

Access mode:
- BULK;
- MANUAL;
- page-based resource discovery.

Update cadence: Quarterly, with revisions possible.

Live state on 2026-09-27:
- October 2026 Medicare Part B Payment Limit File: Final, posted 2026-09-17;
- October 2026 NDC-HCPCS Crosswalk: Final, posted 2026-09-17.

Prefer discovery from the official CMS payment-limit page by effective quarter/year rather than permanently hardcoding a specific ZIP URL.

### Important semantic constraint

A published Part B payment limit is the native CMS payment fact.

Do not automatically relabel every Part B payment limit as ASP. CMS payment-limit files can contain different payment methodologies depending on product/context.

CMS also explicitly states that presence or absence of a HCPCS code, NDC or payment limit in these files does **not** determine Medicare coverage. A MAC may price an eligible product that is absent from a quarterly file.

---

## 4. NDC-HCPCS Crosswalk

Current official October 2026 ZIP:
https://www.cms.gov/files/zip/october-2026-ndc-hcpcs-crosswalk-final.zip

The live archive member list was validated on 2026-09-27.

The October 2026 package contains distinct crosswalk contexts:
- ASP NDC-HCPCS Crosswalk;
- AWP NDC-HCPCS Crosswalk;
- OPPS NDC-HCPCS Crosswalk;
- PrEP NDC-HCPCS Crosswalk;
- introduction/definition material;
- corresponding Section 508 CSV versions.

These files must **not be collapsed into one undifferentiated NDC-HCPCS mapping**. The payment/methodology context is part of the source fact.

For the standard ASP payment-limit relationship, use the ASP crosswalk associated with the Medicare Part B payment-limit publication.

### Official ASP crosswalk columns

CMS's March 9, 2026 ASP publication FAQ defines the HCPCS/NDC crosswalk columns as:

- `HCPCS Level II Code defer to DCDRG`;
- `Short Description defer to DCDRG`;
- `Labeler Name`;
- `NDC2`;
- `Drug Name`;
- `HCPCS Dosage`;
- `PKG SIZE`;
- `PKG QTY`;
- `BILLUNITS`;
- `BILLUNITSPKG`.

Official FAQ:
https://www.cms.gov/files/document/frequently-asked-questions-faqs-asp-data-collection.pdf

### Identifier semantics

CMS defines `NDC2` as an 11-digit NDC shown in hyphenated form, identifying the specific product/package.

This makes the ASP crosswalk an especially strong bridge to the project's NDC identity layer:

```text
source FDA NDC segments
      ↓ deterministic CMS11 representation
5-4-2 hyphenated NDC
      ↓ exact official crosswalk
HCPCS
```

Keep:
- raw crosswalk NDC;
- parsed NDC segments;
- derived CMS11 representation;
- HCPCS;
- effective quarter;
- crosswalk subtype/context;
- source publication/revision date.

### Unit semantics

The crosswalk explicitly contains the conversion structure between package and HCPCS billing units:

- `HCPCS Dosage` = amount represented by one HCPCS billing unit;
- `PKG SIZE` = quantity in one container/item;
- `PKG QTY` = number of containers/items in the package;
- `BILLUNITS` = HCPCS billing units in one container/item;
- `BILLUNITSPKG` = HCPCS billing units in the entire NDC package.

These conversion fields are important for Part B quantity normalization. They must not be confused with pharmacy pricing units such as NADAC unit types.

### Current validation boundary

The October 2026 archive membership and the official 2026 ASP crosswalk schema were validated directly.

A full row-level duplicate/cardinality test of the current October CSV should still be performed when the adapter is implemented. Do not assume one-to-one NDC↔HCPCS cardinality merely from the existence of the crosswalk.

---

## 5. HCPCS code reference

CMS publishes quarterly HCPCS code-system updates.

Official page:
https://www.cms.gov/medicare/coding-billing/healthcare-common-procedure-system/quarterly-update

Role:
- HCPCS code identity;
- descriptor/reference context;
- code status/effective updates.

This is complementary to the NDC-HCPCS crosswalk. The crosswalk supplies the package-to-billing-code relationship; the HCPCS files supply code-system context.

---

## Useful outputs / KPIs

Potential future outputs include:
- NDC ↔ HCPCS coverage/mapping;
- package-to-billing-unit conversion;
- HCPCS payment-limit trend;
- annual and preliminary Part B spending trend;
- claims and beneficiary counts;
- spending per claim/beneficiary/dosage unit;
- HCPCS-to-drug portfolio mapping;
- crosswalk changes by effective quarter;
- new NDC/HCPCS appearance monitoring.

## Core semantic rules

```text
NDC ≠ HCPCS
PACKAGE UNIT ≠ HCPCS BILLING UNIT
PAYMENT LIMIT ≠ ACQUISITION COST
PAYMENT LIMIT FILE PRESENCE ≠ COVERAGE
QUARTERLY REFRESH ≠ SINGLE-QUARTER FACT
ASP / AWP / OPPS / PrEP CROSSWALKS ≠ ONE SEMANTIC SOURCE
```
