from concurrent.futures import ThreadPoolExecutor, as_completed
from ingest import fetch_openalex_papers, fetch_nsf_sbir_awards, fetch_sbir_gov
from score import score_items
from database import upsert_leads, fetch_existing_ids
from config import ENABLE_OPENALEX, ENABLE_NSF_SBIR, ENABLE_SBIR_GOV

def run_pipeline():
    print("=" * 50)
    print("Fetch pipeline starting...")

    existing_ids = fetch_existing_ids()
    print(f"Skipping {len(existing_ids)} existing records in database")

    # Fetch all enabled sources in parallel
    fetch_tasks = {}
    if ENABLE_OPENALEX:
        fetch_tasks["openalex"] = fetch_openalex_papers
    if ENABLE_NSF_SBIR:
        fetch_tasks["nsf"] = fetch_nsf_sbir_awards
    if ENABLE_SBIR_GOV:
        fetch_tasks["sbir_gov"] = fetch_sbir_gov

    fetched = {}
    with ThreadPoolExecutor(max_workers=len(fetch_tasks) or 1) as executor:
        futures = {executor.submit(fn): name for name, fn in fetch_tasks.items()}
        for future in as_completed(futures):
            name = futures[future]
            try:
                fetched[name] = future.result()
            except Exception as e:
                print(f"  Fetch error [{name}]: {e}")
                fetched[name] = []

    source_labels = {"openalex": "OpenAlex", "nsf": "NSF SBIR", "sbir_gov": "SBIR.gov"}

    def process_source(name, items):
        label = source_labels[name]
        new_items = [p for p in items if p["paper_id"] not in existing_ids]
        print(f"{label}: {len(items)} fetched, {len(new_items)} new")
        scored = score_items(new_items)
        upsert_leads(scored)
        print(f"Scored {len(scored)} {label} leads: {sum(1 for l in scored if l.get('relevance_score', 0) >= 7)} scored 7+")
        return scored

    all_leads = []
    with ThreadPoolExecutor(max_workers=len(fetched) or 1) as executor:
        futures = {executor.submit(process_source, name, items): name for name, items in fetched.items()}
        for future in as_completed(futures):
            try:
                all_leads.extend(future.result())
            except Exception as e:
                print(f"  Error processing [{futures[future]}]: {e}")

    high_signal = sorted(
        [l for l in all_leads if l.get("relevance_score", 0) >= 7],
        key=lambda x: x["relevance_score"],
        reverse=True,
    )

    print("\n" + "=" * 50)
    print("Pipeline complete")
    print(f"Total scored: {len(all_leads)}")
    print(f"High signal (7+): {len(high_signal)}")
    print("=" * 50)

    if high_signal:
        print("\nTOP LEADS:")
        for lead in high_signal[:5]:
            print(f"[{lead['relevance_score']}/10] [{lead['source']}] {lead['title'][:70]}")
            print(f"{lead['why_this_matters'][:120]}...")
            print()

if __name__ == "__main__":
    run_pipeline()
