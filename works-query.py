import requests
import pandas as pd
import time

INSTITUTION_ID = "i1925986|i1304196042"  # IDs for Loyola University Chicago and Loyola University Medical Center

def get_doaj_info(issn, cache={}):
    """
    Query DOAJ API for journal-level OA and APC information.
    Only returns data for fully gold OA journals listed in DOAJ.
    Results are cached per ISSN to avoid duplicate requests.
    """
    if not issn:
        return {}
    if issn in cache:
        return cache[issn]
    try:
        r = requests.get(
            f"https://doaj.org/api/search/journals/issn:{issn}",
            timeout=10
        )
        r.raise_for_status()
        data = r.json()

        results = data.get("results", [])
        if not results:
            cache[issn] = {}
            return {}

        # take the first result
        journal = results[0]
        bibjson = journal.get("bibjson", {})
        apc = bibjson.get("apc", {})
        waiver = bibjson.get("waiver", {})
        license_list = bibjson.get("license", [])

        result = {
            "doaj_in_doaj": journal.get("admin", {}).get("ticked"),
            "doaj_apc_has_apc": apc.get("has_apc"),
            "doaj_apc_waiver": waiver.get("has_waiver"),
            "doaj_apc_max_value": apc.get("max", [{}])[0].get("price") if apc.get("max") else None,
            "doaj_apc_currency": apc.get("max", [{}])[0].get("currency") if apc.get("max") else None,
            "doaj_license": license_list[0].get("type") if license_list else None,
        }
        cache[issn] = result
        time.sleep(0.5)
        return result
    except Exception as e:
        print(f"DOAJ lookup failed for ISSN {issn}: {e}")
        cache[issn] = {}
        return {}

def get_works(institution_id, year=2021):
    """
    Fetches all works from OpenAlex for a given institution and year.
    Uses cursor-based pagination to retrieve all results beyond the 200-per-page limit.
    """
    works = []
    cursor = "*"
    
    while cursor:
        params = {
            "filter": f"authorships.institutions.id:{institution_id},publication_year:{year}",
            "select": "id,display_name,publication_year,publication_date,doi,type,authorships,primary_topic,open_access,primary_location,apc_list,apc_paid,funders",
            "per-page": 200,
            "cursor": cursor,
            "mailto": "gmartin5@luc.edu"  # polite pool = faster responses
        }
        
        r = requests.get("https://api.openalex.org/works", params=params)
        r.raise_for_status()
        data = r.json()
        
        results = data.get("results", [])
        if not results:
            break
        
        works.extend(results)
        cursor = data.get("meta", {}).get("next_cursor")
        print(f"Fetched {len(works)} works so far...")
    
    return works

def parse_works(works):
    """
    Flattens raw OpenAlex work objects into a tidy table.
    Also performs journal-level DOAJ lookups per unique ISSN.
    """
    rows = []
    for w in works:
        if not w.get("id"):
            continue

        pt = w.get("primary_topic") or {}
        sf = pt.get("subfield") or {}
        field = pt.get("field") or {}
        domain = pt.get("domain") or {}
        oa = w.get("open_access") or {}
        loc = w.get("primary_location") or {}
        source = loc.get("source") or {}
        apc = w.get("apc_paid") or {}
        cost = w.get("apc_list") or {}
        funders = w.get("funders") or []
        funder_ids = [f["id"] for f in funders if f.get("id")]
        funder_names = [f["display_name"] for f in funders if f.get("display_name")]

        authors = [
            {
                "name": a["author"]["display_name"],
                "affiliations": a.get("raw_affiliation_strings", [])
            }
            for a in w.get("authorships", [])
            if a.get("author") and a["author"].get("display_name")
        ]

        institutions = [
            inst["display_name"]
            for a in w.get("authorships", [])
            for inst in a.get("institutions", [])
            if inst.get("display_name") is not None
        ]

        institution_rors = [
            inst["ror"]
            for a in w.get("authorships", [])
            for inst in a.get("institutions", [])
            if inst.get("ror") is not None
        ]

        institution_types = [
            inst["type"]
            for a in w.get("authorships", [])
            for inst in a.get("institutions", [])
            if inst.get("type") is not None
        ]

        affiliation = [
            s
            for a in w.get("authorships", [])
            for s in a.get("raw_affiliation_strings", [])
        ]

        # journal-level DOAJ lookup — cached per ISSN so each journal is only queried once
        issn = source.get("issn_l")
        doaj = get_doaj_info(issn)

        rows.append({
            # article identifiers
            "openalex_id": w.get("id"),
            "title": w.get("display_name"),
            "year": w.get("publication_year"),
            "publication_date": w.get("publication_date"),
            "doi": w.get("doi"),
            "type": w.get("type"),
            # authorship
            "authors": "; ".join(a["name"] for a in authors),
            "institutions": "; ".join(set(institutions)),
            "raw_institution": "; ".join(affiliation),
            "institution_rors": "; ".join(set(institution_rors)),
            "institution_types": "; ".join(set(institution_types)),
            # open access
            "oa_status": oa.get("oa_status"),
            "is_oa": oa.get("is_oa"),
            "license": loc.get("license"),  # article-level license
            # journal/source
            "source_name": source.get("display_name"),
            "source_type": source.get("type"),
            "issn": issn,
            "publisher": source.get("host_organization_name"),
            # topic classification
            "subfield_name": sf.get("display_name"),
            "field_name": field.get("display_name"),
            "domain_name": domain.get("display_name"),
            # APC data from OpenAlex
            "apc_paid_value": apc.get("value"),
            "apc_paid_currency": apc.get("currency"),
            "apc_paid_value_usd": apc.get("value_usd"),
            "apc_paid_provenance": apc.get("provenance"),
            "apc_cost_value": cost.get("value"),
            "apc_cost_currency": cost.get("currency"),
            "apc_cost_usd": cost.get("value_usd"),
            "apc_cost_provenance": cost.get("provenance"),
            # funders
            "funder_ids": "; ".join(funder_ids),
            "funder_names": "; ".join(funder_names),
            # DOAJ journal-level data (only populated for gold OA journals)
            "doaj_in_doaj": doaj.get("doaj_in_doaj"),
            "doaj_apc_has_apc": doaj.get("doaj_apc_has_apc"),
            "doaj_apc_waiver": doaj.get("doaj_apc_waiver"),
            "doaj_apc_max_value": doaj.get("doaj_apc_max_value"),
            "doaj_apc_currency": doaj.get("doaj_apc_currency"),
            "doaj_license": doaj.get("doaj_license"),
        })

    return pd.DataFrame(rows)

# Ask for year input
year = int(input("Enter the publication year to query: "))

works = get_works(INSTITUTION_ID, year=year)
df = parse_works(works)
df.to_csv(f"works_{year}-publisher.csv", index=False)
print(f"Done! {len(df)} works saved to works_{year}-publisher.csv")
