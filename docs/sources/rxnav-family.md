# RxNav / RxNorm Source Family

Status: ADOPTED AS SOURCE FAMILY
Owner: U.S. National Library of Medicine
Last live validation: 2026-09-27

## Core role

RxNav is an official semantic, terminology and crosswalk layer rather than a package-level identity authority.

## Adopted components

### RxNorm API
Use for:
- NDC ↔ RxCUI relationships;
- ingredient concepts;
- branded and generic clinical drug concepts;
- strength and quantity;
- dose form;
- NDA and SPL SetID properties where supplied;
- concept relationships.

An RxCUI may map to multiple package NDCs. It must not replace package/SKU identity.

### RxClass API
Use for semantic/class enrichment such as:
- ATC relationships;
- VA classes;
- FDA pharmacologic classes;
- mechanism-of-action classes;
- MED-RT relationships.

Every class relationship must retain its relationship type and source. A MED-RT relationship must not be silently reinterpreted as an FDA-approved indication.

Some RxClass content, including SNOMED CT-derived content, has additional licensing conditions and must be filtered/handled accordingly.

### RxCUI historical status
Use to understand:
- active/current status;
- activation periods;
- remapping/history;
- historical concept structure.

Useful for longitudinal matching where terminology identifiers change over time.

## Additional access modes

- RxNav UI — manual validation/exploration.
- RxMix — manual/batch workflow exploration and tabular extraction.
- RxNav-in-a-Box — official local/high-volume deployment option.
- Prescribable RxNorm — retained as a future current-prescribable subset/filter.
- RxTerms — deferred display/search enrichment.

## Access constraints

Public RxNav APIs are free and NLM limits requests to 20 per second per IP. Caching is recommended.

## Principle

RxNav enriches and connects identifiers. It does not manufacture package-level precision.
