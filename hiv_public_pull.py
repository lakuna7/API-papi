#!/usr/bin/env python3
"""Pull public U.S. data on HIV antiretrovirals into CSVs and one workbook.

Sources (see docs/sources/ for the contracts each adapter follows):
  1. RxNav             ingredient -> RxCUI
  2. openFDA NDC       products and packages (segmented NDC, CMS11 derived)
  3. CMS Part D        spending by drug, annual + quarterly-refreshed
  4. CMS Part B        spending by drug, annual + quarterly-refreshed
  5. CMS ASP files     NDC-HCPCS crosswalks (ASP/AWP/OPPS/PrEP kept separate)
                       and the Part B payment-limit file

Not pulled: the monthly/quarterly Part D formulary PUFs (multi-GB ZIPs).

Semantics preserved from the source contracts:
  - Spending tables stay at native grain (drug name / HCPCS); they are never
    projected onto NDC packages. Their HIV scope is a name match, recorded in
    `match_basis`.
  - Crosswalk contexts are not collapsed; `crosswalk_context` is kept per row.
  - Payment-limit presence is not a coverage determination.
  - Quarterly spending `Year` labels (e.g. "2025 (Q1-Q4)") are cumulative
    preliminary periods, not single-quarter facts.

Usage:
  python hiv_public_pull.py --out ./out
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import sys
import time
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ---------------------------------------------------------------------------
# Scope
# ---------------------------------------------------------------------------

# Antiretroviral ingredients, by class. Names follow RxNorm/openFDA spelling.
HIV_INGREDIENTS: dict[str, list[str]] = {
    "NRTI": [
        "abacavir", "didanosine", "emtricitabine", "lamivudine", "stavudine",
        "tenofovir alafenamide", "tenofovir disoproxil", "zidovudine",
    ],
    "NNRTI": ["delavirdine", "doravirine", "efavirenz", "etravirine", "nevirapine", "rilpivirine"],
    "PI": [
        "atazanavir", "darunavir", "fosamprenavir", "indinavir", "lopinavir",
        "nelfinavir", "ritonavir", "saquinavir", "tipranavir",
    ],
    "INSTI": ["bictegravir", "cabotegravir", "dolutegravir", "elvitegravir", "raltegravir"],
    "PK_BOOSTER": ["cobicistat"],
    "ENTRY_ATTACHMENT_CAPSID": ["enfuvirtide", "fostemsavir", "ibalizumab", "lenacapavir", "maraviroc"],
}

# A product/row containing any of these is out of scope even if it also contains
# an HIV ingredient (ritonavir in Paxlovid).
EXCLUDE_COINGREDIENTS = ["nirmatrelvir"]

# Brands whose labeled indication is HBV only. Kept, but flagged.
HBV_ONLY_BRANDS = {"VEMLIDY", "EPIVIRHBV"}

OPENFDA_NDC = "https://api.fda.gov/drug/ndc.json"
RXNAV = "https://rxnav.nlm.nih.gov/REST"
CMS_DATA_API = "https://data.cms.gov/data-api/v1/dataset/{id}/data"
CMS_DATASETS = {
    "partd_spending_annual": "7e0b4365-fd63-4a29-8f5e-e0ac9f66a81b",
    "partd_spending_quarterly": "4ff7c618-4e40-483a-b390-c8a58c94fa15",
    "partb_spending_annual": "76a714ad-3a2c-43ac-b76d-9dadf8f7d890",
    "partb_spending_quarterly": "bf6a5b3b-31ee-4abb-b1ad-2607a1e7510a",
}
ASP_HUB = "https://www.cms.gov/medicare/payment/part-b-drugs/asp-pricing-files"
# Validated 2026-09-27 (docs/sources/cms-part-b.md). Used only if discovery fails.
ASP_CROSSWALK_FALLBACK = "https://www.cms.gov/files/zip/october-2026-ndc-hcpcs-crosswalk-final.zip"

USER_AGENT = "API-papi/hiv_public_pull (public-data research)"
SOURCES = ["rxnav", "openfda", "partd", "partb", "asp"]


def all_ingredients() -> list[str]:
    return [i for group in HIV_INGREDIENTS.values() for i in group]


def ingredient_class() -> dict[str, str]:
    return {i: cls for cls, group in HIV_INGREDIENTS.items() for i in group}


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------


class Fetcher:
    def __init__(self, raw_dir: Path, openfda_key: str | None = None):
        self.raw_dir = raw_dir
        self.openfda_key = openfda_key
        self.s = requests.Session()
        self.s.headers["User-Agent"] = USER_AGENT
        retry = Retry(total=5, connect=1, backoff_factor=1.5, status_forcelist=(429, 500, 502, 503, 504),
                      allowed_methods=("GET",), respect_retry_after_header=True)
        self.s.mount("https://", HTTPAdapter(max_retries=retry))

    def get(self, url: str, params: dict | None = None, timeout: int = 120) -> requests.Response:
        return self.s.get(url, params=params, timeout=timeout)

    def get_json(self, url: str, params: dict | None = None):
        r = self.get(url, params)
        r.raise_for_status()
        return r.json()

    def get_text(self, url: str) -> str:
        r = self.get(url)
        r.raise_for_status()
        return r.text

    def get_bytes(self, url: str) -> bytes:
        r = self.get(url, timeout=600)
        r.raise_for_status()
        return r.content

    def save_raw(self, name: str, data: bytes | str | object) -> Path:
        p = self.raw_dir / name
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, bytes):
            p.write_bytes(data)
        elif isinstance(data, str):
            p.write_text(data, encoding="utf-8")
        else:
            p.write_text(json.dumps(data, indent=1, default=str), encoding="utf-8")
        return p


# ---------------------------------------------------------------------------
# Identifier and name helpers
# ---------------------------------------------------------------------------


def norm_name(s: object) -> str:
    """Uppercase alphanumerics only."""
    return re.sub(r"[^A-Z0-9]", "", str(s or "").upper())


def parse_ndc(raw: object) -> dict:
    """Parse a hyphenated NDC. Never infers segmentation from bare digits (ADR-0001)."""
    raw_s = str(raw or "").strip()
    out = {"ndc_raw": raw_s, "labeler": None, "product": None, "package": None,
           "ndc_cms11": None, "ndc_fda12": None}
    parts = raw_s.split("-")
    if len(parts) not in (2, 3) or not all(p.isdigit() for p in parts):
        return out
    lab, prod = parts[0], parts[1]
    pkg = parts[2] if len(parts) == 3 else None
    out.update(labeler=lab, product=prod, package=pkg)
    if pkg is not None:
        if len(lab) <= 5 and len(prod) <= 4 and len(pkg) <= 2:
            out["ndc_cms11"] = f"{lab.zfill(5)}-{prod.zfill(4)}-{pkg.zfill(2)}"
        if len(lab) <= 6 and len(prod) <= 4 and len(pkg) <= 2:
            out["ndc_fda12"] = f"{lab.zfill(6)}-{prod.zfill(4)}-{pkg.zfill(2)}"
    return out


def cms11_from_crosswalk(raw: object) -> str | None:
    """CMS NDC2 is 11-digit 5-4-2, hyphenated or not; 11 digits is unambiguous here."""
    s = str(raw or "").strip()
    if re.fullmatch(r"\d{5}-\d{4}-\d{2}", s):
        return s
    d = re.sub(r"\D", "", s)
    if len(d) == 11:
        return f"{d[:5]}-{d[5:9]}-{d[9:]}"
    if len(d) == 10 and s.isdigit():
        # A leading zero dropped by a spreadsheet; the file declares 11 digits.
        d = "0" + d
        return f"{d[:5]}-{d[5:9]}-{d[9:]}"
    return None


class NameMatcher:
    """Matches CMS drug-name fields (often truncated, '/'-joined) to HIV scope."""

    def __init__(self, ingredients: list[str], brands: set[str]):
        self.ingr = {norm_name(i): i for i in ingredients}
        self.ingr_words = {i: self._words(i) for i in ingredients}
        self.excl_words = [self._words(x) for x in EXCLUDE_COINGREDIENTS]
        self.excl = [norm_name(x) for x in EXCLUDE_COINGREDIENTS]
        self.brands = {norm_name(b) for b in brands if norm_name(b)}

    @staticmethod
    def _words(s: object) -> list[str]:
        return re.findall(r"[A-Z0-9]+", str(s or "").upper())

    @staticmethod
    def _word_prefix_match(tok: list[str], ref: list[str]) -> bool:
        """Word-wise prefix match; handles CMS truncation like 'Tenofov Ala'."""
        if not tok or len(tok[0]) < 4:
            return False
        return all(a.startswith(b) or b.startswith(a) for a, b in zip(tok, ref))

    def _token_hits(self, text: object) -> tuple[list[str], bool]:
        hits, excluded = [], False
        for tok in re.split(r"[/,;&]|\bAND\b", str(text or "").upper()):
            w = self._words(tok)
            if any(self._word_prefix_match(w, x) for x in self.excl_words):
                excluded = True
                continue
            hits += [i for i, iw in self.ingr_words.items() if self._word_prefix_match(w, iw)]
        return sorted(set(hits)), excluded

    def _substring_hits(self, text: object) -> tuple[list[str], bool]:
        t = norm_name(text)
        excluded = any(x in t for x in self.excl)
        return sorted({i for ni, i in self.ingr.items() if ni in t}), excluded

    def match(self, brand: object = None, generic: object = None, desc: object = None) -> dict:
        basis, ingr, excluded = [], set(), False
        if brand is not None and norm_name(brand) in self.brands:
            basis.append("brand")
        if generic is not None:
            h, ex = self._token_hits(generic)
            excluded |= ex
            if h:
                basis.append("generic")
                ingr.update(h)
        if desc is not None:
            h, ex = self._substring_hits(desc)
            excluded |= ex
            if h:
                basis.append("description")
                ingr.update(h)
        return {"matched": bool(basis) and not excluded, "match_basis": ";".join(basis),
                "matched_ingredients": ";".join(sorted(ingr)), "excluded_coingredient": excluded}


def hbv_only(brand: object) -> bool:
    return norm_name(brand) in HBV_ONLY_BRANDS


# ---------------------------------------------------------------------------
# Adapters
# ---------------------------------------------------------------------------


@dataclass
class Result:
    tables: dict[str, pd.DataFrame] = field(default_factory=dict)
    manifest: list[dict] = field(default_factory=list)

    def log(self, source: str, status: str, **kw):
        row = {"source": source, "status": status,
               "retrieved_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), **kw}
        self.manifest.append(row)
        extra = " ".join(f"{k}={v}" for k, v in kw.items() if k != "urls")
        print(f"[{status:5}] {source} {extra}", file=sys.stderr)


def pull_rxnav(f: Fetcher, res: Result) -> None:
    cls = ingredient_class()
    rows = []
    for ingr in all_ingredients():
        ids = []
        try:
            j = f.get_json(f"{RXNAV}/rxcui.json", {"name": ingr, "search": 2})
            ids = (j.get("idGroup") or {}).get("rxnormId") or []
        except requests.ConnectionError:
            raise  # host unreachable: fail the source, not each ingredient
        except requests.RequestException as e:
            rows.append({"ingredient": ingr, "class": cls[ingr], "rxcui": None, "error": str(e)})
            continue
        if not ids:
            rows.append({"ingredient": ingr, "class": cls[ingr], "rxcui": None, "error": "no RxCUI"})
        for rxcui in ids:
            props = {}
            try:
                props = f.get_json(f"{RXNAV}/rxcui/{rxcui}/properties.json").get("properties") or {}
            except requests.RequestException:
                pass
            rows.append({"ingredient": ingr, "class": cls[ingr], "rxcui": rxcui,
                         "rxnorm_name": props.get("name"), "tty": props.get("tty"), "error": None})
        time.sleep(0.1)  # NLM limit: 20 req/s/IP
    df = pd.DataFrame(rows)
    res.tables["rxnav_ingredients"] = df
    res.log("rxnav", "ok", rows=len(df), unresolved=int(df["rxcui"].isna().sum()), urls=RXNAV)


def _openfda_search(f: Fetcher, query: str) -> list[dict]:
    out, skip, limit = [], 0, 1000
    while True:
        params = {"search": query, "limit": limit, "skip": skip}
        if f.openfda_key:
            params["api_key"] = f.openfda_key
        r = f.get(OPENFDA_NDC, params)
        if r.status_code == 404:  # openFDA returns 404 NOT_FOUND for zero hits
            break
        r.raise_for_status()
        batch = r.json().get("results") or []
        out.extend(batch)
        total = ((r.json().get("meta") or {}).get("results") or {}).get("total", 0)
        skip += limit
        if len(batch) < limit or skip >= total or skip >= 25000:
            break
    return out


def pull_openfda(f: Fetcher, res: Result, include_unfinished: bool) -> None:
    cls = ingredient_class()
    by_product: dict[str, dict] = {}
    hits: dict[str, set[str]] = {}
    for ingr in all_ingredients():
        q = f'(generic_name:"{ingr}" OR active_ingredients.name:"{ingr}")'
        for rec in _openfda_search(f, q):
            pid = rec.get("product_id") or rec.get("product_ndc")
            by_product[pid] = rec
            hits.setdefault(pid, set()).add(ingr)
        time.sleep(0.3)  # 240 req/min without key
    f.save_raw("openfda_ndc_products.json", list(by_product.values()))

    excl = [norm_name(x) for x in EXCLUDE_COINGREDIENTS]
    products, packages, dropped = [], [], []
    for pid, rec in by_product.items():
        ai = rec.get("active_ingredients") or []
        ai_names = [a.get("name", "") for a in ai]
        row = {
            "product_id": pid,
            "product_ndc": rec.get("product_ndc"),
            "brand_name": rec.get("brand_name"),
            "generic_name": rec.get("generic_name"),
            "labeler_name": rec.get("labeler_name"),
            "dosage_form": rec.get("dosage_form"),
            "route": ";".join(rec.get("route") or []),
            "active_ingredients": "; ".join(f"{a.get('name')} {a.get('strength')}" for a in ai),
            "matched_ingredients": ";".join(sorted(hits[pid])),
            "hiv_classes": ";".join(sorted({cls[i] for i in hits[pid]})),
            "product_type": rec.get("product_type"),
            "marketing_category": rec.get("marketing_category"),
            "application_number": rec.get("application_number"),
            "marketing_start_date": rec.get("marketing_start_date"),
            "marketing_end_date": rec.get("marketing_end_date"),
            "listing_expiration_date": rec.get("listing_expiration_date"),
            "finished": rec.get("finished"),
            "rxcui": ";".join((rec.get("openfda") or {}).get("rxcui") or []),
            "spl_set_id": ";".join((rec.get("openfda") or {}).get("spl_set_id") or []),
            "pharm_class_epc": ";".join(rec.get("pharm_class") or []),
            "hbv_only_brand": hbv_only(rec.get("brand_name")),
        }
        if any(x in norm_name(n) for n in ai_names for x in excl):
            dropped.append({**row, "drop_reason": "excluded co-ingredient"})
            continue
        if not include_unfinished and rec.get("finished") is False:
            dropped.append({**row, "drop_reason": "unfinished (bulk/API ingredient)"})
            continue
        products.append(row)
        for pkg in rec.get("packaging") or []:
            p = parse_ndc(pkg.get("package_ndc"))
            packages.append({
                "product_id": pid,
                "product_ndc": rec.get("product_ndc"),
                "package_ndc": pkg.get("package_ndc"),
                "ndc_labeler": p["labeler"], "ndc_product": p["product"], "ndc_package": p["package"],
                "ndc_cms11": p["ndc_cms11"], "ndc_fda12": p["ndc_fda12"],
                "ndc_cms11_match_class": "CMS11_DERIVED" if p["ndc_cms11"] else "UNRESOLVED",
                "package_description": pkg.get("description"),
                "package_marketing_start_date": pkg.get("marketing_start_date"),
                "package_marketing_end_date": pkg.get("marketing_end_date"),
                "sample": pkg.get("sample"),
                "brand_name": rec.get("brand_name"),
                "generic_name": rec.get("generic_name"),
                "labeler_name": rec.get("labeler_name"),
                "matched_ingredients": row["matched_ingredients"],
                "hbv_only_brand": row["hbv_only_brand"],
            })
    res.tables["fda_ndc_products"] = pd.DataFrame(products)
    res.tables["fda_ndc_packages"] = pd.DataFrame(packages)
    if dropped:
        res.tables["fda_ndc_dropped"] = pd.DataFrame(dropped)
    res.log("openfda", "ok", products=len(products), packages=len(packages), dropped=len(dropped),
            urls=OPENFDA_NDC)


def _cms_dataset(f: Fetcher, dataset_id: str) -> list[dict]:
    url, out, offset, size = CMS_DATA_API.format(id=dataset_id), [], 0, 5000
    while True:
        batch = f.get_json(url, {"size": size, "offset": offset})
        if not batch:
            break
        out.extend(batch)
        if len(batch) < size:
            break
        offset += size
    return out


def pull_cms_spending(f: Fetcher, res: Result, key: str, matcher: NameMatcher, hcpcs: set[str]) -> None:
    ds = CMS_DATASETS[key]
    rows = _cms_dataset(f, ds)
    f.save_raw(f"{key}_full.json", rows)
    df = pd.DataFrame(rows)
    if df.empty:
        res.log(key, "warn", rows=0, note="dataset returned no rows")
        return
    m = df.apply(lambda r: matcher.match(r.get("Brnd_Name"), r.get("Gnrc_Name"), r.get("HCPCS_Desc")),
                 axis=1, result_type="expand")
    if "HCPCS_Cd" in df.columns and hcpcs:
        cw = df["HCPCS_Cd"].astype(str).str.strip().isin(hcpcs)
        m["match_basis"] = [";".join(filter(None, [b, "crosswalk_hcpcs" if c else ""]))
                            for b, c in zip(m["match_basis"], cw)]
        m["matched"] = m["matched"] | (cw & ~m["excluded_coingredient"])
    df = pd.concat([df, m], axis=1)
    df["hbv_only_brand"] = df.get("Brnd_Name", pd.Series(dtype=str)).map(hbv_only)
    out = df[df["matched"]].drop(columns=["matched"]).reset_index(drop=True)
    res.tables[key] = out
    res.log(key, "ok", source_rows=len(df), hiv_rows=len(out), urls=CMS_DATA_API.format(id=ds))


# ---- ASP / crosswalk -------------------------------------------------------

_MONTHS = {"january": 1, "april": 4, "july": 7, "october": 10}


def _zip_rank(url: str) -> tuple:
    n = url.lower().rsplit("/", 1)[-1]
    m = re.search(r"(january|april|july|october)[-_ ]?(\d{4})", n)
    m2 = re.search(r"(\d{4})[-_ ]?(january|april|july|october)", n)
    if m:
        year, month = int(m.group(2)), _MONTHS[m.group(1)]
    elif m2:
        year, month = int(m2.group(1)), _MONTHS[m2.group(2)]
    else:
        year, month = 0, 0
    return (year, month, "final" in n, any(k in n for k in ("revised", "corrected", "updated")))


def discover_asp_zips(f: Fetcher) -> dict[str, str]:
    """Latest crosswalk and payment-limit ZIPs from the CMS hub (one level deep)."""
    html = f.get_text(ASP_HUB)
    pages = [ASP_HUB]
    links = set(re.findall(r'href="([^"]+)"', html))
    zips = {urljoin(ASP_HUB, h) for h in links if h.lower().endswith(".zip")}
    if not zips:
        sub = {urljoin(ASP_HUB, h) for h in links
               if "asp-pricing-files/" in h or re.search(r"(january|april|july|october)-\d{4}", h)}
        for u in sorted(sub)[:40]:
            try:
                zips |= {urljoin(u, h) for h in re.findall(r'href="([^"]+\.zip)"', f.get_text(u), re.I)}
                pages.append(u)
            except requests.RequestException:
                continue
    cw = [z for z in zips if "crosswalk" in z.lower()]
    pl = [z for z in zips if not re.search(r"crosswalk|noc", z.lower())
          and re.search(r"asp-pricing|payment-limit|pricing-file", z.lower())]
    return {"crosswalk": max(cw, key=_zip_rank) if cw else None,
            "payment_limit": max(pl, key=_zip_rank) if pl else None,
            "pages": pages}


def _read_table_with_header(data: bytes, name: str, header_tokens: list[str]) -> pd.DataFrame | None:
    """Read a CSV/XLSX whose real header may sit below title rows."""
    lname = name.lower()
    if lname.endswith((".xlsx", ".xls")):
        raw = pd.read_excel(io.BytesIO(data), header=None, dtype=str)
    elif lname.endswith((".csv", ".txt")):
        text = None
        for enc in ("utf-8-sig", "cp1252", "latin-1"):
            try:
                text = data.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        rows = list(csv.reader(io.StringIO(text)))
        width = max((len(r) for r in rows), default=0)
        raw = pd.DataFrame([r + [""] * (width - len(r)) for r in rows], dtype=str)
    else:
        return None
    for i in range(min(len(raw), 30)):
        cells = [norm_name(c) for c in raw.iloc[i].tolist() if norm_name(c) and str(c) != "nan"]
        if len(cells) >= 3 and all(any(t in c for c in cells) for t in header_tokens):
            df = raw.iloc[i + 1:].copy()
            df.columns = [str(c).strip() for c in raw.iloc[i].tolist()]
            df = df.loc[:, [c for c in df.columns if c and c.lower() != "nan"]]
            return df.dropna(how="all").reset_index(drop=True)
    return None


def _crosswalk_context(member: str) -> str:
    n = member.upper()
    for ctx in ("PREP", "OPPS", "AWP", "ASP"):
        if ctx in n:
            return ctx
    return "UNKNOWN"


def _col(df: pd.DataFrame, *tokens: str) -> str | None:
    for c in df.columns:
        if all(t in norm_name(c) for t in tokens):
            return c
    return None


def pull_asp(f: Fetcher, res: Result, cms11_set: set[str], matcher: NameMatcher,
             crosswalk_url: str | None, payment_limit_url: str | None) -> set[str]:
    """Returns HIV HCPCS codes found in crosswalks and the payment-limit file."""
    disc: dict = {}
    if not (crosswalk_url and payment_limit_url):
        try:
            disc = discover_asp_zips(f)
        except requests.RequestException as e:
            res.log("asp_discovery", "error", error=str(e), urls=ASP_HUB)
    crosswalk_url = crosswalk_url or disc.get("crosswalk") or ASP_CROSSWALK_FALLBACK
    payment_limit_url = payment_limit_url or disc.get("payment_limit")
    hcpcs: set[str] = set()

    # Crosswalk
    try:
        blob = f.get_bytes(crosswalk_url)
        f.save_raw("asp/" + crosswalk_url.rsplit("/", 1)[-1], blob)
        zf = zipfile.ZipFile(io.BytesIO(blob))
        members = zf.namelist()
        seen_ctx: set[str] = set()
        # Prefer the Section 508 CSVs; fall back to XLSX per context.
        ordered = sorted(members, key=lambda m: (not m.lower().endswith(".csv"), m))
        for mem in ordered:
            ctx = _crosswalk_context(mem)
            if ctx == "UNKNOWN" or ctx in seen_ctx:
                continue
            df = _read_table_with_header(zf.read(mem), mem, ["HCPCS", "NDC"])
            if df is None or df.empty:
                continue
            seen_ctx.add(ctx)
            ndc_c = _col(df, "NDC")
            hc_c = _col(df, "HCPCS")
            name_c = _col(df, "DRUG", "NAME")
            df.insert(0, "crosswalk_context", ctx)
            df.insert(1, "source_member", mem)
            df["ndc_cms11"] = df[ndc_c].map(cms11_from_crosswalk) if ndc_c else None
            df["in_fda_hiv_ndc_set"] = df["ndc_cms11"].isin(cms11_set)
            nm = df[name_c].map(lambda s: matcher.match(generic=s, desc=s)) if name_c else None
            df["drug_name_match"] = [x["matched"] for x in nm] if nm is not None else False
            df["match_basis"] = [";".join(filter(None, ["ndc_cms11" if a else "", "drug_name" if b else ""]))
                                 for a, b in zip(df["in_fda_hiv_ndc_set"], df["drug_name_match"])]
            keep = df["in_fda_hiv_ndc_set"] | df["drug_name_match"]
            if ctx == "PREP":
                keep[:] = True  # the PrEP crosswalk is HIV-scoped by definition
            sel = df[keep].copy()
            if hc_c:
                sel = sel.rename(columns={hc_c: "hcpcs_code"})
                hcpcs |= {h.strip() for h in sel["hcpcs_code"].astype(str) if h.strip()}
            res.tables[f"crosswalk_{ctx.lower()}"] = sel.reset_index(drop=True)
            # Cardinality check the contract asks for, reported, not enforced.
            if ndc_c and hc_c:
                dup = df.groupby("ndc_cms11")[hc_c].nunique()
                res.log(f"crosswalk_{ctx.lower()}", "info", rows=len(df), hiv_rows=len(sel),
                        ndcs_with_multiple_hcpcs=int((dup > 1).sum()))
        res.log("asp_crosswalk", "ok", contexts=",".join(sorted(seen_ctx)), members=len(members),
                hiv_hcpcs=len(hcpcs), urls=crosswalk_url)
    except (requests.RequestException, zipfile.BadZipFile) as e:
        res.log("asp_crosswalk", "error", error=str(e), urls=crosswalk_url)

    # Payment limits
    if not payment_limit_url:
        res.log("asp_payment_limit", "warn", note="no payment-limit ZIP discovered; pass --payment-limit-url")
        return hcpcs
    try:
        blob = f.get_bytes(payment_limit_url)
        f.save_raw("asp/" + payment_limit_url.rsplit("/", 1)[-1], blob)
        zf = zipfile.ZipFile(io.BytesIO(blob))
        pl = None
        for mem in sorted(zf.namelist(), key=lambda m: (not m.lower().endswith(".csv"), m)):
            if "crosswalk" in mem.lower():
                continue
            pl = _read_table_with_header(zf.read(mem), mem, ["HCPCS", "PAYMENT"])
            if pl is not None and not pl.empty:
                pl.insert(0, "source_member", mem)
                break
        if pl is None:
            res.log("asp_payment_limit", "warn", note="no payment-limit table found in ZIP", urls=payment_limit_url)
            return hcpcs
        hc_c = _col(pl, "HCPCS")
        desc_c = _col(pl, "DESCRIPTION") or _col(pl, "DESC")
        none = pd.Series(False, index=pl.index)
        by_code = pl[hc_c].astype(str).str.strip().isin(hcpcs) if hc_c else none
        by_desc = pl[desc_c].map(lambda s: matcher.match(desc=s)["matched"]).astype(bool) if desc_c else none
        keep = by_code | by_desc
        sel = pl[keep].copy()
        sel["match_basis"] = [";".join(filter(None, ["crosswalk_hcpcs" if a else "", "description" if b else ""]))
                              for a, b in zip(by_code[keep], by_desc[keep])]
        res.tables["asp_payment_limit"] = sel.reset_index(drop=True)
        if hc_c:
            hcpcs |= {h.strip() for h in sel[hc_c].astype(str) if h.strip()}
        res.log("asp_payment_limit", "ok", rows=len(pl), hiv_rows=len(sel), urls=payment_limit_url)
    except (requests.RequestException, zipfile.BadZipFile) as e:
        res.log("asp_payment_limit", "error", error=str(e), urls=payment_limit_url)
    return hcpcs


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

NOTES = [
    ("Scope", "HIV antiretroviral ingredients listed in hiv_public_pull.py; products containing "
              + ", ".join(EXCLUDE_COINGREDIENTS) + " excluded."),
    ("hbv_only_brand", "Flags brands labeled for HBV only (e.g. Vemlidy, Epivir-HBV). Kept, not dropped."),
    ("Spending tables", "Native grain is drug name (Part D) or HCPCS (Part B). HIV scope is a name/HCPCS "
                        "match shown in match_basis. Never allocate to NDC packages."),
    ("Quarterly spending", "Year labels like '2025 (Q1-Q4)' are cumulative preliminary periods."),
    ("Part D names", "Part D spending has one row per manufacturer plus an 'Overall' row per drug; do not sum both."),
    ("Crosswalks", "ASP/AWP/OPPS/PrEP contexts kept separate. PrEP crosswalk kept whole."),
    ("Payment limit", "A payment limit is not acquisition cost and presence is not a coverage determination."),
    ("NDC", "ndc_cms11 derived segment-wise from hyphenated FDA NDCs (ADR-0001); UNRESOLVED if not derivable."),
    ("Not pulled", "Part D formulary PUFs (multi-GB), Medicaid NADAC/SDUD, FAERS, labels."),
]


def write_outputs(out: Path, res: Result) -> Path:
    for name, df in res.tables.items():
        df.to_csv(out / f"{name}.csv", index=False)
    (out / "manifest.json").write_text(json.dumps(res.manifest, indent=1, default=str), encoding="utf-8")
    xlsx = out / "hiv_public_pull.xlsx"
    with pd.ExcelWriter(xlsx, engine="openpyxl") as xw:
        pd.DataFrame(NOTES, columns=["topic", "note"]).to_excel(xw, sheet_name="README", index=False)
        pd.DataFrame(res.manifest).to_excel(xw, sheet_name="manifest", index=False)
        for name, df in res.tables.items():
            df.to_excel(xw, sheet_name=name[:31], index=False)
        for ws in xw.book.worksheets:
            ws.freeze_panes = "A2"
            for col in ws.columns:
                width = max((len(str(c.value)) for c in list(col)[:200] if c.value is not None), default=8)
                ws.column_dimensions[col[0].column_letter].width = min(max(width + 2, 8), 60)
    return xlsx


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", type=Path, default=Path("./out"))
    ap.add_argument("--skip", nargs="*", default=[], choices=SOURCES, help="sources to skip")
    ap.add_argument("--crosswalk-url", help="override the NDC-HCPCS crosswalk ZIP URL")
    ap.add_argument("--payment-limit-url", help="override the Part B payment-limit ZIP URL")
    ap.add_argument("--include-unfinished", action="store_true",
                    help="keep openFDA unfinished (bulk ingredient) listings")
    ap.add_argument("--openfda-api-key", default=os.environ.get("OPENFDA_API_KEY"))
    a = ap.parse_args(argv)

    a.out.mkdir(parents=True, exist_ok=True)
    f = Fetcher(a.out / "raw", a.openfda_api_key)
    res = Result()

    def run(name: str, fn, *args):
        if name.split("_")[0] in a.skip:
            res.log(name, "skip")
            return None
        try:
            return fn(*args)
        except Exception as e:  # keep going; the manifest records the failure
            res.log(name, "error", error=f"{type(e).__name__}: {e}")
            return None

    run("rxnav", pull_rxnav, f, res)
    run("openfda", pull_openfda, f, res, a.include_unfinished)

    pk = res.tables.get("fda_ndc_packages", pd.DataFrame())
    cms11 = set(pk["ndc_cms11"].dropna()) if "ndc_cms11" in pk else set()
    pr = res.tables.get("fda_ndc_products", pd.DataFrame())
    brands = set(pr["brand_name"].dropna()) if "brand_name" in pr else set()
    matcher = NameMatcher(all_ingredients(), brands)

    hcpcs = run("asp", pull_asp, f, res, cms11, matcher, a.crosswalk_url, a.payment_limit_url) or set()
    for key in CMS_DATASETS:
        run(key, pull_cms_spending, f, res, key, matcher, hcpcs if key.startswith("partb") else set())

    xlsx = write_outputs(a.out, res)
    errors = [m for m in res.manifest if m["status"] == "error"]
    print(f"\nWrote {len(res.tables)} tables to {a.out.resolve()} ({xlsx.name}); "
          f"{len(errors)} source error(s).", file=sys.stderr)
    return 2 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
