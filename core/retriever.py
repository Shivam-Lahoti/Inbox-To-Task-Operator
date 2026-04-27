from core.vector_store import SimpleVectorStore


def retrieve_context(
    query: str,
    chunks: list[dict],
    top_k: int = 5
) -> list[dict]:
    store = SimpleVectorStore()
    store.build(chunks)
    store.save_metadata()

    return store.search(query=query, top_k=top_k)