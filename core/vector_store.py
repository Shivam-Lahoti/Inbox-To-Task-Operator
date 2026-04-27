import json
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer


INDEX_PATH = Path("storage/vector_index.json")


class SimpleVectorStore:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.chunks = []
        self.matrix = None

    def build(self, chunks: list[dict]):
        self.chunks = chunks
        texts = [chunk["search_text"] for chunk in chunks]
        self.matrix = self.vectorizer.fit_transform(texts)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        from sklearn.metrics.pairwise import cosine_similarity

        if self.matrix is None or not self.chunks:
            return []

        query_vector = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vector, self.matrix).flatten()

        results = []

        for idx, score in enumerate(scores):
            item = self.chunks[idx].copy()
            item["rag_score"] = round(float(score), 3)
            results.append(item)

        return sorted(results, key=lambda x: x["rag_score"], reverse=True)[:top_k]

    def save_metadata(self):
        INDEX_PATH.parent.mkdir(exist_ok=True)

        with open(INDEX_PATH, "w", encoding="utf-8") as f:
            json.dump(self.chunks, f, indent=2)