import anthropic
import json
from config import ANTHROPIC_API_KEY, OPEN_ALEX_PROMPT, NSF_PROMPT, SBIR_GOV_PROMPT

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def score_item(item):
    source = item.get("source")

    if source == "NSF":
        prompt = NSF_PROMPT.format(
            title=item.get("title", "") or "",
            authors=item.get("authors", "") or "",
            institutions=item.get("institutions", "") or "",
            award_amount=item.get("award_amount", "") or "",
            abstract=item.get("abstract", "") or "",
        )
    elif source == "SBIR.gov":
        prompt = SBIR_GOV_PROMPT.format(
            title=item.get("title", "") or "",
            authors=item.get("authors", "") or "",
            institutions=item.get("institutions", "") or "",
            agency=item.get("agency", "") or "",
            phase=item.get("phase", "") or "",
            award_amount=item.get("award_amount", "") or "",
            abstract=item.get("abstract", "") or "",
        )
    elif source == "OpenAlex":
        prompt = OPEN_ALEX_PROMPT.format(
            title=item.get("title", "") or "",
            authors=item.get("authors", "") or "",
            institutions=item.get("institutions", "") or "",
            keywords=item.get("keywords", "") or "",
            funding_source=item.get("funding_source", "") or "",
            abstract=item.get("abstract", "") or "",
        )

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = message.content[0].text

    response_text = response_text.strip()
    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]
    response_text = response_text.strip()

    result = json.loads(response_text)
    return {
        **item,
        "relevance_score": result["relevance_score"],
        "why_this_matters": result["why_this_matters"]
    }


def score_items(items):
    print(f"Scoring {len(items)} items with Claude...")

    scored = []

    for i, item in enumerate(items):
        print(f"  Scoring {i+1}/{len(items)}: {item['title'][:60]}...")
        try:
            scored_item = score_item(item)
            scored.append(scored_item)
        except Exception as e:
            print(f"  Error scoring item: {e}")
            continue

    print(f"Successfully scored {len(scored)} items")
    return scored


if __name__ == "__main__":
    from ingest import fetch_openalex_papers

    items = fetch_openalex_papers()
    scored = score_items(items)

    scored.sort(key=lambda x: x["relevance_score"], reverse=True)

    print(f"\n--- TOP SCORED PAPERS ---")
    for item in scored[:5]:
        print(f"\nScore: {item['relevance_score']}/10")
        print(f"Title: {item['title']}")
        print(f"Why: {item['why_this_matters']}")
