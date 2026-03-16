import anthropic
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import ANTHROPIC_API_KEY, OPEN_ALEX_PROMPT, NSF_PROMPT, SBIR_GOV_PROMPT, MAX_SCORING_WORKERS

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
_claude_semaphore = threading.Semaphore(MAX_SCORING_WORKERS)

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

    for attempt in range(5):
        try:
            with _claude_semaphore:
                message = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=300,
                    messages=[{"role": "user", "content": prompt}]
                )
            break
        except anthropic.RateLimitError:
            if attempt == 4:
                raise
            time.sleep(2 ** attempt)

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
        "why_this_matters": result["why_this_matters"],
    }


def score_items(items, max_workers=MAX_SCORING_WORKERS):
    if not items:
        return []

    scored = []
    print(f"Scoring {len(items)} items with Claude (up to {max_workers} concurrent)...")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(score_item, item): item for item in items}
        for future in as_completed(futures):
            item = futures[future]
            try:
                scored.append(future.result())
            except Exception as e:
                print(f"  Error scoring '{item.get('title', '')[:60]}': {e}")

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
