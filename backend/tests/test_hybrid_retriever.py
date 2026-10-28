import pytest
from app.evidence.doc_ingestion import DocumentChunk
from app.rag.retrieval import HybridRetriever, BM25Retriever, SemanticNgramRetriever

def test_hybrid_retriever_rrf():
    chunks = [
        DocumentChunk(
            chunk_id="chunk-1",
            doc_name="cloud_migration_spec.pdf",
            page_number=4,
            section="Executive Cost Analysis",
            content="Estimated migration cost is $95,000 including staff training and dual-run cloud licenses."
        ),
        DocumentChunk(
            chunk_id="chunk-2",
            doc_name="architecture_audit.docx",
            page_number=12,
            section="Latency & Scaling",
            content="CockroachDB multi-region deployment achieves 99.999% availability with zero downtime schema updates."
        ),
        DocumentChunk(
            chunk_id="chunk-3",
            doc_name="security_review.txt",
            page_number=1,
            section="Compliance",
            content="SOC2 Type II certification and strict GDPR compliance standards must be preserved across storage tiers."
        ),
    ]

    hybrid = HybridRetriever(rrf_k=60)
    hybrid.index_chunks(chunks)

    # 1. Exact & semantic cost query
    results = hybrid.retrieve("What is the projected budget and migration cost?", top_k=2)
    assert len(results) >= 1
    top_chunk, score = results[0]
    assert top_chunk.chunk_id == "chunk-1"
    assert "95,000" in top_chunk.content

    # 2. Availability query
    results_avail = hybrid.retrieve("multi-region database availability target", top_k=1)
    assert len(results_avail) == 1
    assert results_avail[0][0].chunk_id == "chunk-2"

    # 3. Evidence conversion with provenance
    evidence_items = hybrid.retrieve_as_evidence("compliance standards GDPR", top_k=1)
    assert len(evidence_items) == 1
    ev = evidence_items[0]
    assert ev.reliability >= 0.65
    assert "security_review.txt" in ev.source_reference

