"""
RAG & Hybrid Retrieval Layer.
Implements Module 30 (RAG / Knowledge Layer) & Module 6 (Evidence & Provenance).
"""

import math
import re
from typing import Dict, List, Optional, Set, Tuple
from app.evidence.doc_ingestion import DocumentChunk
from app.schemas.entities import Evidence


def tokenize(text: str) -> List[str]:
    return [w.lower() for w in re.findall(r"\w+", text) if len(w) > 2]


class BM25Retriever:
    """
    Lightweight, fast in-memory BM25 index for document chunks with provenance.
    """
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.chunks: List[DocumentChunk] = []
        self.doc_len: List[int] = []
        self.avg_doc_len: float = 0.0
        self.doc_freqs: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.term_freqs: List[Dict[str, int]] = []

    def index_chunks(self, chunks: List[DocumentChunk]) -> None:
        self.chunks.extend(chunks)
        total_len = 0
        
        for chunk in chunks:
            tokens = tokenize(chunk.content)
            self.doc_len.append(len(tokens))
            total_len += len(tokens)
            
            tf: Dict[str, int] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            self.term_freqs.append(tf)

            for t in set(tokens):
                self.doc_freqs[t] = self.doc_freqs.get(t, 0) + 1

        self.avg_doc_len = total_len / len(self.chunks) if self.chunks else 0.0
        num_docs = len(self.chunks)
        for term, freq in self.doc_freqs.items():
            self.idf[term] = math.log(1 + (num_docs - freq + 0.5) / (freq + 0.5))

    def retrieve(self, query: str, top_k: int = 5) -> List[Tuple[DocumentChunk, float]]:
        query_tokens = tokenize(query)
        if not query_tokens or not self.chunks:
            return []

        scores: List[float] = [0.0] * len(self.chunks)

        for token in query_tokens:
            if token not in self.idf:
                continue
            token_idf = self.idf[token]
            for idx, tf_dict in enumerate(self.term_freqs):
                if token in tf_dict:
                    freq = tf_dict[token]
                    doc_l = self.doc_len[idx]
                    denom = freq + self.k1 * (1 - self.b + self.b * (doc_l / (self.avg_doc_len or 1)))
                    scores[idx] += token_idf * (freq * (self.k1 + 1)) / (denom or 1.0)

        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        results = []
        for i in ranked_indices[:top_k]:
            if scores[i] > 0.0:
                results.append((self.chunks[i], scores[i]))

        return results

    def retrieve_as_evidence(self, query: str, top_k: int = 3) -> List[Evidence]:
        results = self.retrieve(query, top_k=top_k)
        evidence_list = []
        for chunk, score in results:
            normalized_score = min(0.95, max(0.5, score / 10.0))
            evidence_list.append(chunk.to_evidence(reliability=normalized_score))
        return evidence_list
