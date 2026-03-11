# Reveille VC Deal Scout

> AI-powered deal sourcing pipeline for defense and energy venture capital

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat&logo=python&logoColor=white)
![Claude](https://img.shields.io/badge/Claude-Haiku-D97706?style=flat)
![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?style=flat&logo=supabase&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?style=flat&logo=streamlit&logoColor=white)

```
┌──────────────────────────────────────────────────────────────────┐
│                           main.py                                │
│                         Orchestrator                             │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                          ingest.py                               │
│                                                                  │
│   ┌─────────────────────────┐   ┌─────────────────────────────┐  │
│   │      OpenAlex API       │   │    NSF SBIR Grants API      │  │
│   │    Academic Papers      │   │      Funded Startups        │  │
│   │      7-day window       │   │       30-day window         │  │
│   └─────────────────────────┘   └─────────────────────────────┘  │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                          filter.py                               │
│         Rule-based pre-filter — abstract length + dedup          │
│                    Reduces Claude API costs 80%+                 │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                           score.py                               │
│     Claude Haiku — 1-10 relevance score + investment rationale   │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                          database.py                             │
│     Supabase PostgreSQL — upsert on paper_id, no duplicates      │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                           app.py                                 │
│   All Leads │ Research Signals │ Funded Companies │ Signal Brief │
└──────────────────────────────────────────────────────────────────┘
```

---

## Overview

Early-stage VC deal sourcing relies on conferences, referrals, and manually reading publications — slow, network-biased, and impossible to scale. This pipeline automates the entire process, giving a small fund the sourcing capacity of a team ten times its size.

Built for [Reveille VC](https://www.reveillevc.com) — a NYC-based $25M debut fund investing in defense and energy. Configurable for any fund thesis via `config.py` without touching pipeline code.

**Features:**
- Two live data sources — academic papers (OpenAlex) and federally funded startups (NSF SBIR)
- 80%+ reduction in Claude API costs via rule-based pre-filtering before any LLM processing
- Claude Haiku scores each record against a configurable fund thesis with a 1–10 score and 2–3 sentence rationale
- Upsert-on-conflict persistence — safe to run daily without creating duplicates
- Multi-tab Streamlit dashboard with lead status management
- SBIR.gov integration implemented and ready — enable by setting `ENABLE_SBIR_GOV=True` in `config.py` once the program API is restored

---

## Architecture

```
reveille-scout/
├── main.py          # Orchestrator — runs all four pipeline stages
├── ingest.py        # OpenAlex + NSF SBIR REST API ingestion
├── filter.py        # Rule-based pre-filter before LLM processing
├── score.py         # Claude Haiku scoring with error handling
├── database.py      # Supabase upsert, fetch, and status updates
├── app.py           # Streamlit multi-tab dashboard
├── config.py        # Pipeline settings and search configuration
├── .env             # API credentials and secrets (gitignored)
├── .env.example     # Credentials template — copy to .env to get started
├── requirements.txt # anthropic, supabase, streamlit, requests
└── .gitignore
```

---

## Data Sources

| Source | Status | Lookback | Best For |
|--------|--------|----------|----------|
| OpenAlex | ✅ Active | 7 days | Research signals, authors to contact |
| NSF SBIR Grants | ✅ Active | 30 days | Fundable companies with PI email + award amount |
| SBIR.gov | ⏸️ Disabled | 30 days | DOD/DOE/NASA funded startups (March 2026) |

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

Create a Supabase project, run the table schema in the SQL Editor, then fill in `.env` with your credentials.

---

## Configuration

Credentials live in `.env` (gitignored). Pipeline behavior is controlled from `config.py` — change search terms, thesis, and lookback windows to redeploy for any fund.

**`.env`**

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase anon public key |

**`config.py`**

| Field | Type | Description |
|-------|------|-------------|
| `SEARCH_TERMS` | list[list[str]] | OpenAlex terms — inner list AND-joined, outer list OR-joined |
| `NSF_FILTER_KEYWORDS` | list[str] | Keywords validated against NSF abstracts post-fetch |
| `OPEN_ALEX_DAYS_BACK` | int | OpenAlex lookback window (default: 7) |
| `NSF_DAYS_BACK` | int | NSF SBIR lookback window (default: 30) |
| `RESULTS_PER_SEARCH` | int | Max results per OpenAlex search term (default: 10) |
| `EMAIL` | str | Passed to OpenAlex as a courtesy identifier |

---

## Usage

**Run the pipeline:**
```bash
python3 main.py
```

```
==================================================
REVEILLE DEAL SCOUT — PIPELINE STARTING
==================================================

[1/4] INGESTING...
Fetched 28 valid papers from OpenAlex
Fetched 11 relevant NSF SBIR grants
Total ingested: 39 (28 OpenAlex, 11 NSF)

[2/4] FILTERING...
After filter: 32 leads

[3/4] SCORING...
Scored 32 leads — 9 scored 7+

[4/4] SAVING TO SUPABASE...
Upserted 32 leads to Supabase

==================================================
PIPELINE COMPLETE — 9 high signal leads (7+)
==================================================

TOP LEADS:
  [9/10] Grid-scale solid-state battery for military microgrids
  [8/10] Autonomous counter-UAS detection via passive RF analysis
```

**Launch the dashboard:**
```bash
streamlit run app.py
```

---

## License

MIT © 2026 Samay Shah

---

## Author

**Samay Shah** — CS, University of Michigan

[samayms@umich.edu](mailto:samayms@umich.edu) · [github.com/samayms](https://github.com/samayms) · [LinkedIn](https://linkedin.com/in/samayshah)
