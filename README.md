# Reveille VC Deal Scout

> AI-powered deal sourcing pipeline for defense and energy venture capital

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat&logo=python&logoColor=white)
![Claude](https://img.shields.io/badge/Claude-Haiku-D97706?style=flat)
![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?style=flat&logo=supabase&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?style=flat&logo=streamlit&logoColor=white)

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                                    main.py                                       │
│                         Parallel fetch + score + persist                         │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                                   ingest.py                                      │
│                                                                                  │
│            ┌─────────────────────────┐   ┌─────────────────────────────┐         │
│            │      OpenAlex API       │   │    NSF SBIR Grants API      │         │
│            │    Academic Papers      │   │      Funded Startups        │         │
│            │      7-day window       │   │      180-day window         │         │
│            └─────────────────────────┘   └─────────────────────────────┘         │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                                   score.py                                       │
│            Claude Haiku — 1-10 relevance score + investment rationale            │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                                  database.py                                     │
│            Supabase PostgreSQL: upsert on paper_id, no duplicates                │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                                    app.py                                        │
│  Signal Brief │ All Leads │ Research Signals │ Funded Companies │ Federal Grants │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## Overview

Early-stage VC deal sourcing relies on conferences, referrals, and manually reading publications which is slow, network-biased, and impossible to scale. This pipeline automates the entire process, giving a small fund the sourcing capacity of a team ten times its size.

Built for [Reveille VC](https://www.reveillevc.com), a NYC-based $25M debut fund investing in defense and energy. Configurable for any fund thesis via `config.py` without touching pipeline code.

**Live app:** [reveille-deal-scout.streamlit.app](https://reveille-deal-scout.streamlit.app)

**Features:**
- Two live data sources: academic papers (OpenAlex) and federally funded startups (NSF SBIR), plus optional SBIR.gov ingestion
- Parallel multi-source fetch orchestration and concurrent Claude scoring with global semaphore rate limiting and exponential backoff
- 90%+ estimated reduction in LLM calls via rule-based keyword and abstract validation before scoring
- Existing-record skips before scoring to avoid rescoring leads already stored in Supabase
- OpenAlex abstract reconstruction from inverted-index responses before downstream scoring
- Source-specific scoring prompts for OpenAlex, NSF SBIR, and SBIR.gov records
- Claude Haiku scores each record against a configurable fund thesis with a 1-10 score and 2-3 sentence rationale
- OpenAlex lead enrichment with authors, institutions, keywords, funding source, venue, record type, publication date, and citation count
- NSF/SBIR lead enrichment with PI contact info, award amount, company location, grant type, and program metadata
- Upsert-on-conflict persistence; safe to run daily without creating duplicates
- Supabase-backed lead status management (`New`, `Reviewing`, `Pass`)
- Five-tab Streamlit dashboard with Signal Brief, All Leads, Research Signals, Funded Companies, and Federal Grants views
- Dashboard filtering by source, score, and status, plus full lead detail pages
- Live pipeline refresh from the dashboard with cached reads and summary metrics
- SBIR.gov integration implemented and ready; enable by setting `ENABLE_SBIR_GOV=True` in `config.py` once the program API is restored

---

## Architecture

```
reveille-scout/
├── main.py          # Parallel fetch orchestration, scoring, and persistence
├── ingest.py        # OpenAlex + NSF SBIR REST API ingestion and validation
├── score.py         # Claude Haiku scoring with error handling
├── database.py      # Supabase upsert, fetch, and status updates
├── app.py           # Streamlit multi-tab dashboard
├── config.py        # Pipeline settings and search configuration
├── .env             # API credentials and secrets (gitignored)
├── .env.example     # Credentials template — copy to .env to get started
├── requirements.txt # anthropic, supabase, requests, streamlit, pandas
└── .gitignore
```

---

## Data Sources

| Source | Status | Lookback | Best For |
|--------|--------|----------|----------|
| OpenAlex | Active | 7 days | Research signals, authors to contact |
| NSF SBIR Grants | Active | 180 days | Fundable companies with PI email + award amount |
| SBIR.gov | Disabled | Current + prior year pagination | DOD/DOE funded startups (March 2026) |

---

## Requirements

- Python 3.9+
- [Anthropic API key](https://console.anthropic.com)
- [Supabase project](https://supabase.com) (free tier sufficient)

---

## Installation

```bash
git clone https://github.com/samayms/reveille-scout
cd reveille-scout
pip install -r requirements.txt
cp .env.example .env
```

Create a Supabase project, create the `items` table used by `database.py`, then fill in `.env` with your credentials.

---

## Configuration

Credentials live in `.env` (gitignored). Pipeline behavior is controlled from `config.py`. There, change search terms, thesis, and lookback windows to redeploy for any fund.

**`.env`**

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase anon public key |
| `EMAIL` | Optional contact email sent to OpenAlex as a courtesy identifier |

**`config.py`**

| Field | Type | Description |
|-------|------|-------------|
| `ENABLE_OPENALEX` | bool | Toggle OpenAlex ingestion |
| `ENABLE_NSF_SBIR` | bool | Toggle NSF SBIR/STTR ingestion |
| `ENABLE_SBIR_GOV` | bool | Toggle SBIR.gov ingestion |
| `SEARCH_TERMS` | list[list[str]] | OpenAlex terms; inner list AND-joined, outer list OR-joined |
| `NSF_FILTER_KEYWORDS` | list[str] | Keywords validated against NSF abstracts post-fetch |
| `OPEN_ALEX_DAYS_BACK` | int | OpenAlex lookback window (default: 7) |
| `NSF_DAYS_BACK` | int | NSF SBIR lookback window (default: 365) |
| `RESULTS_PER_SEARCH` | int | Max results per OpenAlex search term (default: 20) |
| `MAX_SCORING_WORKERS` | int | Max concurrent Claude scoring threads (default: 5, safe for Tier 1 50 RPM limit) |
| `NSF_PROGRAM_NAMES` | list[str] | NSF program filters, currently `SBIR` and `STTR` |

---

## Usage

**Run the pipeline:**
```bash
python3 main.py
```

```
==================================================
Fetch pipeline starting...
==================================================
Found 142 existing records in database — skipping these.
Fetching papers from OpenAlex...
Fetching NSF SBIR grants...
OpenAlex: 28 fetched, 6 new
Scoring 6 items with Claude (up to 5 concurrent)...
Successfully scored 6 items
Upserted 6 leads to Supabase
Scored 6 OpenAlex papers: 2 scored 7+
NSF SBIR: 11 fetched, 4 new
Scoring 4 items with Claude (up to 5 concurrent)...
Successfully scored 4 items
Upserted 4 leads to Supabase
Scored 4 NSF leads: 1 scored 7+

==================================================
Pipeline complete
Total scored: 10
High signal (7+): 3
==================================================
```

**Launch the dashboard:**
```bash
streamlit run app.py
```

**Live deployment:**  
[https://reveille-deal-scout.streamlit.app](https://reveille-deal-scout.streamlit.app)

---

## License

MIT © 2026 Samay Shah

---

## Author

**Samay Shah**: CS, University of Michigan

[samayms@umich.edu](mailto:samayms@umich.edu) | [github.com/samayms](https://github.com/samayms) | [LinkedIn](https://www.linkedin.com/in/samay-shah-19a4911b0/)
