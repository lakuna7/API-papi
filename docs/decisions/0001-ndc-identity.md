# ADR-0001 — NDC Identity and Hierarchical Matching

Status: Accepted
Date: 2026-09-27

## Decision

The system will preserve source-native NDCs and their segment structure rather than treating a single padded NDC-11 value as the permanent master identifier.

NDC identity is hierarchical:

- labeler segment identifies the labeler;
- labeler + product segments identify the product;
- labeler + product + package segments identify the package/SKU level.

The system will support segment-aware normalization and hierarchical matching across sources.

## Canonical future form

Where the source NDC segmentation is known, each segment can be deterministically left-padded to FDA's uniform 12-digit 6-4-2 structure:

```text
labeler-product-package
XXXXXX-XXXX-XX
```

Example conceptually:

```text
legacy segmented NDC
0002-0243-04

future-form normalized representation
000002-0243-04
```

Hyphens are preserved in the normalized segmented representation because they retain the identifier hierarchy and make transformations auditable.

A digits-only representation may also be generated for systems that require one, but it is derived and must not replace the segmented form.

## Important constraint

Do not infer legacy NDC segmentation from a bare unhyphenated 10-digit value by length alone.

Legacy FDA NDCs can use different segment patterns. Deterministic padding to 6-4-2 requires known segmentation from the source, FDA metadata, or another validated official mapping.

Ambiguous identifiers remain unresolved until segmentation is validated.

## Identifier representations

For an NDC, retain where available:

- raw/source identifier;
- raw source formatting;
- parsed labeler segment;
- parsed product segment;
- parsed package segment;
- normalized segmented representation;
- normalized digits-only representation;
- derived CMS 11-digit representation where applicable;
- future-form FDA 12-digit 6-4-2 representation where deterministically derivable;
- provenance for every transformation.

## Match validation

Initial match classes:

- EXACT_SOURCE — exact source identifier and formatting match.
- EXACT_SEGMENTED — same validated labeler/product/package segments despite formatting differences.
- HIERARCHICAL_PRODUCT — validated match at labeler + product level when package is not available.
- HIERARCHICAL_LABELER — validated labeler-level relationship only.
- CMS11_DERIVED — deterministic transformation to CMS 11-digit form.
- FDA12_DERIVED — deterministic segment-wise transformation to FDA 6-4-2 form.
- OFFICIAL_CROSSWALK — relationship supplied by an official mapping source such as RxNorm or DailyMed.
- MULTI_MATCH — more than one defensible candidate; do not silently collapse.
- UNRESOLVED — no defensible match.

A lower-grain match must never be presented as package-level evidence.

## Adopted identity-source roles

- FDA NDC Directory — authoritative drug listing / identity source.
- openFDA NDC API — preferred live API/query representation of FDA NDC Directory data.
- RxNorm / RxNav — NDC-to-RxCUI and terminology crosswalk layer, not the identity authority.
- DailyMed — SPL/label identity, packaging, SetID/version history, and cross-validation layer.

## Principle

Preserve first, normalize second, match at the highest defensible shared grain, and never manufacture precision that the source did not provide.
