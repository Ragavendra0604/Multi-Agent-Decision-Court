"""
RAG & Hybrid Retrieval Layer.
Implements Module 30 (RAG / Knowledge Layer) & Module 6 (Evidence & Provenance).
Combines Sparse BM25 Lexical Ranking + Semantic Similarity with Reciprocal Rank Fusion (RRF).
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
            normalized_score = min(0.95, max(0.65, round(score / 10.0 + 0.65, 2)))
            evidence_list.append(chunk.to_evidence(reliability=normalized_score))
        return evidence_list


class SemanticNgramRetriever:
    """
    Sub-word semantic retriever using character and word n-gram Jaccard / Cosine overlap.
    Captures morphological variations, acronyms, and semantic stems that BM25 misses.
    """
    def __init__(self, n: int = 3):
        self.n = n
        self.chunks: List[DocumentChunk] = []
        self.chunk_ngrams: List[Set[str]] = []

    def _extract_ngrams(self, text: str) -> Set[str]:
        words = tokenize(text)
        grams = set()
        for w in words:
            grams.add(w)
            if len(w) >= self.n:
                for i in range(len(w) - self.n + 1):
                    grams.add(w[i:i + self.n])
        return grams

    def index_chunks(self, chunks: List[DocumentChunk]) -> None:
        self.chunks.extend(chunks)
        for c in chunks:
            self.chunk_ngrams.append(self._extract_ngrams(c.content))

    def retrieve(self, query: str, top_k: int = 5) -> List[Tuple[DocumentChunk, float]]:
        q_grams = self._extract_ngrams(query)
        if not q_grams or not self.chunks:
            return []

        scored: List[Tuple[DocumentChunk, float]] = []
        for c, doc_grams in zip(self.chunks, self.chunk_ngrams):
            if not doc_grams:
                continue
            intersection = len(q_grams.intersection(doc_grams))
            union = len(q_grams.union(doc_grams))
            jaccard = intersection / union if union > 0 else 0.0
            if jaccard > 0:
                scored.append((c, jaccard))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]


class HybridRetriever:
    """
    Unified Hybrid Retrieval Engine combining BM25 keyword matching and
    Semantic N-gram similarity via Reciprocal Rank Fusion (RRF).
    Guarantees both keyword precision and semantic recall.
    """
    def __init__(self, rrf_k: int = 60):
        self.rrf_k = rrf_k
        self.bm25 = BM25Retriever()
        self.semantic = SemanticNgramRetriever()
        self.chunks: List[DocumentChunk] = []

    def index_chunks(self, chunks: List[DocumentChunk]) -> None:
        self.chunks.extend(chunks)
        self.bm25.index_chunks(chunks)
        self.semantic.index_chunks(chunks)

    def retrieve(self, query: str, top_k: int = 5) -> List[Tuple[DocumentChunk, float]]:
        if not self.chunks:
            return []

        bm25_hits = self.bm25.retrieve(query, top_k=top_k * 2)
        semantic_hits = self.semantic.retrieve(query, top_k=top_k * 2)

        # Reciprocal Rank Fusion Score: RRF = sum(1 / (k + rank))
        rrf_scores: Dict[str, float] = {}
        chunk_lookup: Dict[str, DocumentChunk] = {}

        for rank, (chunk, _) in enumerate(bm25_hits):
            chunk_lookup[chunk.chunk_id] = chunk
            rrf_scores[chunk.chunk_id] = rrf_scores.get(chunk.chunk_id, 0.0) + (1.0 / (self.rrf_k + rank + 1))

        for rank, (chunk, _) in enumerate(semantic_hits):
            chunk_lookup[chunk.chunk_id] = chunk
            rrf_scores[chunk.chunk_id] = rrf_scores.get(chunk.chunk_id, 0.0) + (1.0 / (self.rrf_k + rank + 1))

        ranked = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        
        results: List[Tuple[DocumentChunk, float]] = []
        for chunk_id, score in ranked[:top_k]:
            results.append((chunk_lookup[chunk_id], score))

        return results

    def retrieve_as_evidence(self, query: str, top_k: int = 3) -> List[Evidence]:
        results = self.retrieve(query, top_k=top_k)
        evidence_list = []
        for chunk, score in results:
            # Normalize RRF score (scale ~0.015 - 0.033 to 0.70 - 0.95 reliability)
            normalized_score = min(0.95, max(0.65, round(score * 30.0, 2)))
            evidence_list.append(chunk.to_evidence(reliability=normalized_score))
        return evidence_list
