"""Semantic search over facts, literature abstracts and curated mineral notes.

Backends:
- "chroma": sentence-transformers (all-MiniLM-L6-v2) embeddings in a persistent ChromaDB
  collection. Install with `pip install -r requirements-semantic.txt`.
- "lsa": TF-IDF + truncated SVD (latent semantic analysis) with cosine similarity. Pure
  scikit-learn, no model download, used automatically when the above is unavailable.

Select explicitly with KE_SEARCH_BACKEND=chroma|lsa.
"""
from __future__ import annotations

import json
import os
import re

import numpy as np

from .config import CHROMA_DIR, KNOWLEDGE_SEED, LITERATURE_METADATA
from .facts import load_facts

EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def corpus_documents(facts: list[dict] | None = None) -> list[dict]:
    """Every searchable unit as {id, text, kind, metadata}."""
    facts = facts if facts is not None else load_facts()
    docs = [{"id": fact["id"], "text": fact["text"], "kind": "fact",
             "metadata": {"system": fact["system"], "property": fact["property"], "material": fact["material"],
                          "family": fact["material_family"], "record_id": fact["record_id"],
                          "doi": fact["source"].get("doi") or "", "africa_score": fact["africa"]["score"] or 0.0}}
            for fact in facts]
    if KNOWLEDGE_SEED.exists():
        for i, chunk in enumerate(re.split(r"\n(?=## )", KNOWLEDGE_SEED.read_text(encoding="utf-8"))):
            if chunk.strip() and not chunk.startswith("# "):
                title = chunk.splitlines()[0].lstrip("# ").strip()
                docs.append({"id": f"note-{i}", "text": chunk.strip(), "kind": "note",
                             "metadata": {"system": "context", "property": "", "material": title, "family": "",
                                          "record_id": "", "doi": "", "africa_score": 0.0}})
    if LITERATURE_METADATA.exists():
        for paper in json.loads(LITERATURE_METADATA.read_text(encoding="utf-8")):
            if paper.get("abstract"):
                docs.append({"id": f"paper-{paper.get('doi') or paper.get('id')}",
                             "text": f"{paper.get('title', '')}. {paper['abstract']}", "kind": "paper",
                             "metadata": {"system": paper.get("system", ""), "property": "", "material": "",
                                          "family": "", "record_id": "", "doi": paper.get("doi") or "",
                                          "africa_score": 0.0}})
    return docs


class _LSABackend:
    name = "lsa (TF-IDF + SVD)"

    def __init__(self, docs: list[dict]):
        from sklearn.decomposition import TruncatedSVD
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.pipeline import FeatureUnion
        from sklearn.preprocessing import normalize

        self._normalize = normalize
        # Word n-grams carry meaning; character n-grams keep formulas (Ti3C2Tx, LLZO-0.5Ta) matchable.
        self.vectorizer = FeatureUnion([
            ("words", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, stop_words="english")),
            ("chars", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)),
        ])
        matrix = self.vectorizer.fit_transform([d["text"] for d in docs])
        components = max(2, min(256, matrix.shape[0] - 1, matrix.shape[1] - 1))
        self.svd = TruncatedSVD(n_components=components, random_state=123)
        self.embeddings = normalize(self.svd.fit_transform(matrix))

    def scores(self, query: str) -> np.ndarray:
        vector = self._normalize(self.svd.transform(self.vectorizer.transform([query])))
        return self.embeddings @ vector[0]


class _ChromaBackend:
    name = f"chroma + sentence-transformers ({EMBEDDING_MODEL})"

    def __init__(self, docs: list[dict]):
        import chromadb
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(EMBEDDING_MODEL)
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        try:
            client.delete_collection("materials_facts")
        except Exception:  # collection may not exist yet
            pass
        self.collection = client.create_collection("materials_facts", metadata={"hnsw:space": "cosine"})
        for start in range(0, len(docs), 500):
            batch = docs[start:start + 500]
            self.collection.add(ids=[d["id"] for d in batch], documents=[d["text"] for d in batch],
                                embeddings=self.model.encode([d["text"] for d in batch]).tolist(),
                                metadatas=[{**d["metadata"], "kind": d["kind"]} for d in batch])
        self.ids = [d["id"] for d in docs]

    def scores(self, query: str) -> np.ndarray:
        result = self.collection.query(query_embeddings=self.model.encode([query]).tolist(),
                                       n_results=len(self.ids))
        lookup = {doc_id: 1.0 - distance for doc_id, distance in zip(result["ids"][0], result["distances"][0])}
        return np.array([lookup.get(doc_id, 0.0) for doc_id in self.ids])


class SemanticIndex:
    def __init__(self, docs: list[dict] | None = None, backend: str | None = None):
        self.docs = docs if docs is not None else corpus_documents()
        choice = backend or os.getenv("KE_SEARCH_BACKEND", "auto")
        self.backend = None
        if choice in ("auto", "chroma"):
            try:
                self.backend = _ChromaBackend(self.docs)
            except Exception as exc:  # missing packages or no model download access
                if choice == "chroma":
                    raise
                self.fallback_reason = str(exc)
        if self.backend is None:
            self.backend = _LSABackend(self.docs)

    @property
    def backend_name(self) -> str:
        return self.backend.name

    def search(self, query: str, k: int = 10, system: str | None = None, prop: str | None = None,
               kinds: tuple[str, ...] | None = None, min_africa: float | None = None) -> list[dict]:
        scores = self.backend.scores(query)
        # Light lexical boost so exact formula / dopant mentions rank first.
        terms = {t.lower() for t in re.findall(r"[A-Za-z0-9.\-]{3,}", query)}
        hits = []
        for index in np.argsort(-scores):
            doc = self.docs[index]
            meta = doc["metadata"]
            if system and meta["system"] not in (system, "context"):
                continue
            if prop and meta["property"] != prop:
                continue
            if kinds and doc["kind"] not in kinds:
                continue
            if min_africa is not None and doc["kind"] == "fact" and (meta["africa_score"] or 0) < min_africa:
                continue
            lexical = sum(term in doc["text"].lower() for term in terms) / max(len(terms), 1)
            hits.append({**doc, "score": round(float(scores[index]) + 0.15 * lexical, 4)})
            if len(hits) >= k * 3:
                break
        return sorted(hits, key=lambda hit: -hit["score"])[:k]
