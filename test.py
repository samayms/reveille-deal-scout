import requests
import json

url = "https://api.usaspending.gov/api/v2/search/spending_by_award/"

payload = {
    "filters": {
        "agencies": [
            {"type": "awarding", "tier": "toptier", "name": "Department of Defense"},
            {"type": "awarding", "tier": "toptier", "name": "Department of Energy"}
        ],
        "award_type_codes": ["A", "B", "C", "D"],
        "time_period": [{"start_date": "2025-01-01", "end_date": "2026-03-01"}],
        "keywords": ["autonomous", "solid-state", "directed energy", "neuromorphic"]
    },
    "fields": ["Award ID", "Recipient Name", "Award Amount", "Description", "awarding_agency_name", "period_of_performance_start_date"],
    "page": 1,
    "limit": 5,
    "sort": "Award Amount",
    "order": "desc"
}

response = requests.post(url, json=payload)
data = response.json()
print(json.dumps(data, indent=2))