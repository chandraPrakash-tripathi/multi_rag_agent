from agent.app.core.repository.base import DataRepository


def run_tests():
    repo = DataRepository()

    print("\n" + "=" * 50)
    print("TEST 1: SQL RELATIONAL FETCH (Silver Layer)")
    print("=" * 50)
    events = repo.get_events(limit=3)
    for e in events:
        print(f"[{e['dataset']}] {e['timestamp']} | {e['title']}")

    print("\n" + "=" * 50)
    print("TEST 2: PURE SEMANTIC SEARCH (Vector Layer)")
    print("=" * 50)
    query = "telescope discoveries and space observations"
    print(f"Query: '{query}'")
    unfiltered_results = repo.search_knowledge(query_text=query, limit=3)
    for k in unfiltered_results:
        print(f"[{k['dataset']}] Score: {k['score']:.4f} | {k['title']}")
        print(f"   -> {k['content_preview']}\n")

    print("=" * 50)
    print("TEST 3: HYBRID SEARCH (Semantic + Metadata Filter)")
    print("=" * 50)
    # Using the exact same semantic query, but forcing Qdrant to ONLY look at the 'apod' dataset
    print(f"Query: '{query}'")
    print("Filter: dataset == 'apod'")
    filtered_results = repo.search_knowledge(
        query_text=query, dataset_filter="apod", limit=3
    )
    for k in filtered_results:
        print(f"[{k['dataset']}] Score: {k['score']:.4f} | {k['title']}")
        print(f"   -> {k['content_preview']}\n")


if __name__ == "__main__":
    run_tests()
