from __future__ import annotations

from datetime import datetime, timedelta

import requests

from config import EMAIL, SEARCH_TERMS


def count_openalex_last_week() -> int:
    cutoff = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    total = 0

    for search_term in SEARCH_TERMS:
        params = {
            "search": " ".join(f'"{part}"' for part in search_term),
            "filter": f"from_publication_date:{cutoff}",
            "per-page": 200,
            "mailto": EMAIL,
        }
        response = requests.get("https://api.openalex.org/works", params=params, timeout=30)
        response.raise_for_status()
        results = response.json().get("results", [])
        total += len(results)

    return total


def main() -> None:
    count = count_openalex_last_week()
    print(f"Total OpenAlex articles in the last week: {count}")


if __name__ == "__main__":
    main()
