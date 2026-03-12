from ingest import fetch_openalex_papers, fetch_nsf_sbir_awards, fetch_sbir_gov
from score import score_items
from database import upsert_leads
from config import ENABLE_OPENALEX, ENABLE_NSF_SBIR, ENABLE_SBIR_GOV

def run_pipeline():
    print("=" * 50)
    print("Fetch pipeline starting...")

    all_leads = []

    if ENABLE_OPENALEX:
        openalex_papers = fetch_openalex_papers()
        scored_oa = score_items(openalex_papers)
        upsert_leads(scored_oa)
        high_signal_oa = [l for l in scored_oa if l.get("relevance_score", 0) >= 7]
        print(f"Scored {len(scored_oa)} OpenAlex papers: {len(high_signal_oa)} scored 7+")
        all_leads.extend(scored_oa)

    if ENABLE_NSF_SBIR:
        nsf_leads = fetch_nsf_sbir_awards()
        scored_nsf = score_items(nsf_leads)
        upsert_leads(scored_nsf)
        high_signal_nsf = [l for l in scored_nsf if l.get("relevance_score", 0) >= 7]
        print(f"Scored {len(scored_nsf)} NSF leads: {len(high_signal_nsf)} scored 7+")
        all_leads.extend(scored_nsf)

    if ENABLE_SBIR_GOV:
        sbir_gov_leads = fetch_sbir_gov()
        scored_sbir_gov = score_items(sbir_gov_leads)
        upsert_leads(scored_sbir_gov)
        high_signal_sbir_gov = [l for l in scored_sbir_gov if l.get("relevance_score", 0) >= 7]
        print(f"Scored {len(scored_sbir_gov)} SBIR.gov leads: {len(high_signal_sbir_gov)} scored 7+")
        all_leads.extend(scored_sbir_gov)

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
