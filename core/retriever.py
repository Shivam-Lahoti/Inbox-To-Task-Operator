from typing import List, Dict
from core.vector_store import SimpleVectorStore


def retrieve_context(query: str, chunks: List[Dict], top_k: int = 5) -> List[Dict]:
    """Retrieve most relevant context chunks for a query"""
    store = SimpleVectorStore()
    store.build(chunks)
    store.save_metadata()
    
    return store.search(query=query, top_k=top_k)