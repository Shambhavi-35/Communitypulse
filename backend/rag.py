"""
Lightweight Retrieval-Augmented Generation (RAG) engine.

Production note
----------------
This module stands in for a Gemini + Vertex AI Search / AlloyDB-vector-search
pipeline so the demo runs with zero external API keys. It does real retrieval
(TF-IDF cosine similarity over the knowledge base) and real extractive answer
synthesis - swap `generate_answer()`'s final synthesis step for a Gemini call
(see README) to get fully generative, fluent answers while keeping the same
retrieval contract.
"""
import glob
import os
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

KB_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "knowledge")


class KnowledgeBase:
    def __init__(self, kb_dir=KB_DIR):
        self.docs = []       # list of {"source": filename, "text": full text, "chunks": [...]}
        self.chunk_texts = []  # flattened chunk strings
        self.chunk_meta = []   # (source, chunk_index) per chunk
        self._load(kb_dir)
        self._index()

    def _load(self, kb_dir):
        for path in sorted(glob.glob(os.path.join(kb_dir, "*.txt"))):
            with open(path, "r") as f:
                text = f.read()
            source = os.path.basename(path)
            chunks = self._chunk(text)
            self.docs.append({"source": source, "text": text, "chunks": chunks})
            for i, c in enumerate(chunks):
                if not c.strip():
                    continue
                self.chunk_texts.append(c)
                self.chunk_meta.append((source, i))

    @staticmethod
    def _chunk(text, max_sentences=3):
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        chunks = []
        for i in range(0, len(sentences), max_sentences):
            chunk = " ".join(sentences[i:i + max_sentences]).strip()
            if chunk:
                chunks.append(chunk)
        return chunks

    def _index(self):
        self.vectorizer = TfidfVectorizer(stop_words="english")
        if not self.chunk_texts:
            self.matrix = None
            return
        self.matrix = self.vectorizer.fit_transform(self.chunk_texts)

    def retrieve(self, query, top_k=3):
        if not self.chunk_texts or self.matrix is None:
            return []
        q_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(q_vec, self.matrix)[0]
        ranked = sims.argsort()[::-1][:top_k]
        results = []
        for idx in ranked:
            if sims[idx] <= 0:
                continue
            source, chunk_idx = self.chunk_meta[idx]
            results.append({
                "source": source,
                "text": self.chunk_texts[idx],
                "score": round(float(sims[idx]), 3),
            })
        return results


def generate_answer(kb: KnowledgeBase, question: str, live_context: str = ""):
    """
    Retrieves grounding context, then synthesizes an answer.
    `live_context` lets the caller inject real-time structured data
    (e.g. "Koramangala: 14 dengue-like cases in the last 7 days") so the
    assistant can combine live analytics with static knowledge, the way the
    production Gemini + BigQuery integration would.
    """
    hits = kb.retrieve(question, top_k=3)

    if not hits and not live_context:
        return {
            "answer": "I couldn't find grounded information for that question in the "
                       "current knowledge base. Try rephrasing, or this may need a human "
                       "expert to answer.",
            "sources": [],
        }

    # Extractive synthesis: stitch the most relevant chunks + live data into a
    # single grounded answer. Replace with a Gemini generateContent call for
    # fully fluent, abstractive answers using the same `hits` as context.
    parts = []
    if live_context:
        parts.append(live_context.strip())
    for h in hits:
        parts.append(h["text"])

    answer = " ".join(parts)
    sources = sorted({h["source"] for h in hits})
    return {"answer": answer, "sources": sources, "retrieved_chunks": hits}