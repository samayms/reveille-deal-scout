import requests
import json
from datetime import datetime, timedelta
from config import (
    SEARCH_TERMS,
    RESULTS_PER_SEARCH,
    OPEN_ALEX_DAYS_BACK,
    NSF_DAYS_BACK,
    NSF_FILTER_KEYWORDS,
    NSF_PROGRAM_NAMES,
    ENABLE_OPENALEX,
    ENABLE_NSF_SBIR,
    ENABLE_SBIR_GOV,
    EMAIL,
)

def decode_openalex_abstract(inverted_index):
    if not inverted_index:
        return None
    max_position = max(
        pos
        for positions in inverted_index.values()
        for pos in positions
    )
    words = [""] * (max_position + 1)
    for word, positions in inverted_index.items():
        for pos in positions:
            words[pos] = word
    return " ".join(words)

def fetch_openalex_papers():
    if not ENABLE_OPENALEX:
        print("OpenAlex: disabled (ENABLE_OPENALEX=False)")
        return []
    print("Fetching papers from OpenAlex...")

    one_week_ago = (datetime.now() - timedelta(days=OPEN_ALEX_DAYS_BACK)).strftime("%Y-%m-%d")

    all_papers = []
    seen_titles = set()
    seen_ids = set()

    for search_term in SEARCH_TERMS:
        params = {
            "search": " ".join(f'"{p}"' for p in search_term),
            "filter": f"from_publication_date:{one_week_ago}",
            "per-page": RESULTS_PER_SEARCH,
            # Courtesy request from OpenAlex API
            "mailto": EMAIL
        }

        response = requests.get("https://api.openalex.org/works", params=params)
        data = response.json()

        for work in data.get("results", []):
            paper_id = f"oa_{work.get('id')}"
            title = work.get("title", "") or ""
            if title in seen_titles:
                continue
            seen_titles.add(title)
            abstract = decode_openalex_abstract(work.get("abstract_inverted_index"))

            if not abstract:
                continue

            phrases = [p.lower() for p in search_term]
            content = (title + " " + abstract).lower()
            if not all(phrase in content for phrase in phrases):
                continue

            authors = []
            institutions = []
            for authorship in work.get("authorships", []):
                name = authorship.get("author", {}).get("display_name")
                if name:
                    authors.append(name)
                for inst in authorship.get("institutions", []):
                    inst_name = inst.get("display_name")
                    if inst_name:
                        institutions.append(inst_name)

            funding_source = ", ".join(
                g.get("funder_display_name", "")
                for g in work.get("grants", [])
                if g.get("funder_display_name")
            )

            keywords = ", ".join(
                k.get("keyword", "")
                for k in work.get("keywords", [])
                if k.get("keyword")
            )

            publication_venue = (
                (work.get("primary_location") or {})
                .get("source") or {}
            ).get("display_name", "") or ""

            all_papers.append({
                "paper_id": paper_id,
                "title": title,
                "authors": ", ".join(authors[:3]),
                "institutions": ", ".join(list(set(institutions))[:3]),
                "keywords": keywords,
                "funding_source": funding_source,
                "publication_venue": publication_venue,
                "record_type": work.get("type", ""),
                "abstract": abstract,
                "publication_date": work.get("publication_date"),
                "citation_count": work.get("cited_by_count", 0),
                "source_url": work.get("doi") or paper_id,
                "search_term": " ".join(f'"{p}"' for p in search_term),
                "source": "OpenAlex"
            })

    print(f"Fetched {len(all_papers)} valid papers")
    return all_papers

def fetch_nsf_sbir_awards():
    if not ENABLE_NSF_SBIR:
        print("NSF SBIR: disabled (ENABLE_NSF_SBIR=False)")
        return []
    print("Fetching NSF SBIR grants...")
    url = "http://api.nsf.gov/services/v1/awards.json"
    one_month_ago = (datetime.now() - timedelta(days=NSF_DAYS_BACK)).strftime("%m/%d/%Y")
    companies = []
    seen_ids = set()

    for program in NSF_PROGRAM_NAMES:
        for keyword in NSF_FILTER_KEYWORDS:
            params = {
                "keyword": keyword,
                "fundProgramName": program,
                "dateStart": one_month_ago,
                "printFields": "id,title,abstractText,awardeeName,piEmail,pdPIName,estimatedTotalAmt,startDate,awardeeCity,awardeeStateCode,expDate,awardeePhone,transType,fundProgramName",
                "rpp": 25
            }

            response = requests.get(url, params=params)
            data = response.json()

            awards = data.get("response", {}).get("award", [])
            total = data.get("response", {}).get("metadata", {}).get("totalCount", 0)
            print(f"NSF [{program}] '{keyword}': {total} total grants, processing {len(awards)}")

            for award in awards:
                award_id = f"nsf_{award.get('id')}"

                if award_id in seen_ids:
                    continue
                seen_ids.add(award_id)

                abstract = award.get("abstractText", "") or ""
                title = award.get("title", "") or ""

                content = (title + " " + abstract).lower()
                if not any(kw in content for kw in NSF_FILTER_KEYWORDS):
                    continue

                fn = award.get("fundProgramName", "")
                program = "STTR" if "STTR" in fn else "SBIR"
                if "Fast-Track" in fn:
                    grant_type = f"{program} Fast-Track"
                elif "Phase II" in fn:
                    grant_type = f"{program} Phase II"
                elif "Phase I" in fn:
                    grant_type = f"{program} Phase I"

                companies.append({
                    "paper_id": award_id,
                    "title": title,
                    "authors": award.get("pdPIName", ""),
                    "institutions": award.get("awardeeName", ""),
                    "abstract": abstract,
                    "publication_date": award.get("startDate", ""),
                    "citation_count": 0,
                    "source_url": f"https://www.nsf.gov/awardsearch/showAward?AWD_ID={award.get('id')}",
                    "search_term": f"NSF {program}",
                    "source": "NSF",
                    "pi_email": award.get("piEmail", ""),
                    "award_amount": award.get("estimatedTotalAmt", ""),
                    "company_city": award.get("awardeeCity", ""),
                    "company_state": award.get("awardeeStateCode", ""),
                    "grant_expiry": award.get("expDate", ""),
                    "company_phone": award.get("awardeePhone", ""),
                    "grant_type": grant_type,
                    "fund_program_name": fn,
                })
    
    print(f"Fetched {len(companies)} relevant NSF SBIR grants")
    return companies

def fetch_sbir_gov():
    # NOTE: sbir.gov API is currently offline for maintenance
    # Set ENABLE_SBIR_GOV=True in config.py when restored
    if not ENABLE_SBIR_GOV:
        print("SBIR.gov: disabled (ENABLE_SBIR_GOV=False)")
        return []
    print("Fetching SBIR.gov awards (DOD + DOE)...")

    url = "https://api.www.sbir.gov/public/api/awards"
    current_year = datetime.now().year
    agencies = ["DOD", "DOE"]
    years = [current_year, current_year - 1]
    companies = []
    seen_contracts = set()

    for agency in agencies:
        for year in years:
            start = 0
            page_size = 400
            while True:
                params = {
                    "agency": agency,
                    "year": year,
                    "rows": page_size,
                    "start": start,
                    "format": "json",
                }
                try:
                    response = requests.get(url, params=params, timeout=20)
                    if not response.ok:
                        print(f"SBIR.gov [{agency} {year}]: non-200 response ({response.status_code}) — API may still be in maintenance")
                        break
                    content_type = response.headers.get("Content-Type", "")
                    if "html" in content_type:
                        print(f"SBIR.gov [{agency} {year}]: received HTML instead of JSON — API is in maintenance mode")
                        break
                    awards = response.json()
                except Exception as e:
                    print(f"SBIR.gov [{agency} {year}]: request failed — {e}")
                    break

                if not isinstance(awards, list):
                    print(f"SBIR.gov [{agency} {year}]: unexpected response format")
                    break

                print(f"SBIR.gov [{agency} {year}] offset {start}: {len(awards)} awards returned")

                for award in awards:
                    contract = award.get("contract") or award.get("agency_tracking_number") or ""
                    if not contract or contract in seen_contracts:
                        continue
                    seen_contracts.add(contract)

                    abstract = award.get("abstract", "") or ""
                    title = award.get("award_title", "") or ""

                    if len(abstract.split()) < 100:
                        continue

                    searchable = (title + " " + abstract).lower()
                    if not any(kw in searchable for kw in NSF_FILTER_KEYWORDS):
                        continue

                    fn = (award.get("program", "") or "") + " " + (award.get("phase", "") or "")
                    prefix = "STTR" if "STTR" in fn else "SBIR"
                    if "Fast-Track" in fn:
                        grant_type = f"{prefix} Fast-Track"
                    elif "Phase II" in fn:
                        grant_type = f"{prefix} Phase II"
                    elif "Phase I" in fn:
                        grant_type = f"{prefix} Phase I"
                    else:
                        grant_type = None

                    companies.append({
                        "paper_id": f"sbir_{contract}",
                        "source": "SBIR.gov",
                        "title": title,
                        "abstract": abstract,
                        "authors": award.get("pi_name", ""),
                        "institutions": award.get("firm", ""),
                        "publication_date": award.get("proposal_award_date", ""),
                        "citation_count": 0,
                        "source_url": award.get("award_link", ""),
                        "search_term": "SBIR.gov",
                        "keywords": award.get("research_area_keywords", ""),
                        "pi_email": award.get("pi_email", ""),
                        "poc_email": award.get("poc_email", ""),
                        "poc_phone": award.get("poc_phone", ""),
                        "award_amount": award.get("award_amount", ""),
                        "company_city": award.get("city", ""),
                        "company_state": award.get("state", ""),
                        "company_url": award.get("company_url", ""),
                        "grant_expiry": award.get("contract_end_date", ""),
                        "grant_type": grant_type,
                        "agency": award.get("agency", ""),
                        "branch": award.get("branch", ""),
                        "number_employees": award.get("number_employees", ""),
                    })

                # Stop paginating when we've received the last page
                if len(awards) < page_size:
                    break
                start += page_size

    print(f"Fetched {len(companies)} relevant SBIR.gov awards")
    return companies


if __name__ == "__main__":
    papers = fetch_openalex_papers()
    if papers:
        print(json.dumps(papers[0], indent=2))