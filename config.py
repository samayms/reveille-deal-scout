import os
from pathlib import Path


def _load_env_file():
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


_load_env_file()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPEN_ALEX_KEY = os.getenv("OPEN_ALEX_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_PW = os.getenv("SUPABASE_PW", "")
EMAIL = os.getenv("EMAIL", "")

# --- Data source toggles ---
ENABLE_OPENALEX = True
ENABLE_NSF_SBIR = True  # when sbir.gov API is restored, switch to off as is redundant
ENABLE_SBIR_GOV = False  # sbir.gov API is currently offline; flip to True when restored

SEARCH_TERMS = [
    # POWER — nuclear baseload and grid
    ["small modular reactor", "deployment"],
    ["nuclear microreactor", "military"],
    ["grid modernization", "resilience"],
    ["baseload energy", "decentralized"],

    # PROTECTION — autonomous and unmanned defense
    ["unmanned systems", "defense"],
    ["autonomous defense", "deployment"],
    ["defense industrial base"],

    # PRODUCTIVITY — AI applied to physical economy
    ["AI", "manufacturing", "automation"],
    ["logistics", "autonomous", "military"],
    ["physical economy", "digitization"],
]

RESULTS_PER_SEARCH = 20
MAX_SCORING_WORKERS = 5  # Tier 1: 50 RPM limit; exponential backoff implemented
DAYS_BACK = 7
NSF_DAYS_BACK = 365
OPEN_ALEX_DAYS_BACK = DAYS_BACK
BIG_QUERY_DAYS_BACK = DAYS_BACK
SBIR_GOV_DAYS_BACK = 30

NSF_PROGRAM_NAMES = ["SBIR", "STTR"]

NSF_FILTER_KEYWORDS = [
    # POWER
    "nuclear", "reactor", "microreactor", "grid", "baseload", "smr",
    # PROTECTION
    "defense", "autonomous", "unmanned", "drone", "directed energy", "counter-drone",
    # PRODUCTIVITY
    "manufacturing", "automation", "logistics", "robotics", "supply chain",
]

SBIR_GOV_FILTER_KEYWORDS = [
    # POWER
    "nuclear", "reactor", "microreactor", "grid", "baseload", "smr",
    # PROTECTION
    "defense", "autonomous", "unmanned", "drone", "directed energy", "counter-drone",
    # PRODUCTIVITY
    "manufacturing", "automation", "logistics", "robotics", "supply chain",
]

OPEN_ALEX_PROMPT = """You are an investment analyst for Reveille VC, an early-stage venture capital fund focused on three areas:

POWER: Nuclear energy, small modular reactors, grid modernization, baseload energy, decentralized energy infrastructure
PROTECTION: Autonomous and unmanned defense systems, defense industrial base, counter-drone, directed energy weapons
PRODUCTIVITY: AI applied to physical economy, manufacturing automation, military logistics, supply chain optimization

You are evaluating a research paper to determine if it represents an emerging technology opportunity relevant to Reveille's thesis.

Paper Title: {title}
Authors: {authors}
Institutions: {institutions}
Keywords: {keywords}
Funding: {funding_source}
Abstract: {abstract}

Respond with ONLY a JSON object in this exact format, no other text:
{{
    "relevance_score": <integer 1-10>,
    "why_this_matters": "<2-3 sentences explaining why this is or isn't relevant to Reveille's thesis>"
}}
"""

NSF_PROMPT = """You are an investment analyst for Reveille VC, an early-stage venture capital fund focused on three areas:

POWER: Nuclear energy, small modular reactors, grid modernization, baseload energy, decentralized energy infrastructure
PROTECTION: Autonomous and unmanned defense systems, defense industrial base, counter-drone, directed energy weapons
PRODUCTIVITY: AI applied to physical economy, manufacturing automation, military logistics, supply chain optimization

You are evaluating an NSF SBIR Phase I grant to determine if the company represents an early-stage investment opportunity relevant to Reveille's thesis.

Company: {institutions}
PI: {authors}
Project Title: {title}
Award Amount: {award_amount}
Abstract: {abstract}

Respond with ONLY a JSON object in this exact format, no other text:
{{
    "relevance_score": <integer 1-10>,
    "why_this_matters": "<2-3 sentences explaining why this company is or isn't relevant to Reveille's thesis>"
}}
"""

SBIR_GOV_PROMPT = """You are an investment analyst for Reveille VC, an early-stage venture capital fund focused on three areas:

POWER: Nuclear energy, small modular reactors, grid modernization, baseload energy, decentralized energy infrastructure
PROTECTION: Autonomous and unmanned defense systems, defense industrial base, counter-drone, directed energy weapons
PRODUCTIVITY: AI applied to physical economy, manufacturing automation, military logistics, supply chain optimization

You are evaluating a DoD/federal SBIR/STTR award to determine if the company represents an early-stage investment opportunity relevant to Reveille's thesis.

Company: {institutions}
PI: {authors}
Project Title: {title}
Agency: {agency}
Phase: {phase}
Award Amount: {award_amount}
Abstract: {abstract}

Respond with ONLY a JSON object in this exact format, no other text:
{{
    "relevance_score": <integer 1-10>,
    "why_this_matters": "<2-3 sentences explaining why this company is or isn't relevant to Reveille's thesis>"
}}
"""
