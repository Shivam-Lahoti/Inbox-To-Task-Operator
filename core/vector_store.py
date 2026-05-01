import json
from pathlib import Path
from typing import List, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


STORAGE_DIR = Path("storage")
METADATA_FILE = STORAGE_DIR / "vector_index.json"


class SimpleVectorStore:
    """Simple TF-IDF based vector store for RAG retrieval"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.chunks = []
        self.vectors = None
    
    def build(self, chunks: List[Dict]):
        """Build vector index from chunks"""
        self.chunks = chunks
        
        if not chunks:
            print("⚠️  No chunks to build vector store")
            return
        
        search_texts = [chunk["search_text"] for chunk in chunks]
        self.vectors = self.vectorizer.fit_transform(search_texts)
        
        print(f"✅ Built vector store with {len(chunks)} chunks")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search for most relevant chunks"""
        if not self.chunks or self.vectors is None:
            return []
        
        query_vector = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vector, self.vectors)[0]
        
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0:  # Only return relevant results
                chunk = self.chunks[idx].copy()
                chunk["relevance_score"] = round(float(similarities[idx]), 3)
                results.append(chunk)
        
        return results
    
    def save_metadata(self):
        """Save vector store metadata"""
        STORAGE_DIR.mkdir(exist_ok=True)
        
        metadata = {
            "num_chunks": len(self.chunks),
            "sources": list(set(chunk["source"] for chunk in self.chunks))
        }
        
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)