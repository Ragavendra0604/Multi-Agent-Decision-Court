"""
Document Ingestion & Provenance Extraction.
Implements Module 5 (Document Ingestion), Module 6 (Evidence & Provenance),
and Module 38 (Security & Prompt Injection Sanitization).
"""

from dataclasses import dataclass
import io
import json
import os
import re
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import pypdf
import docx

from app.schemas.enums import ProvenanceType
from app.schemas.entities import Evidence, generate_id


@dataclass
class DocumentChunk:
    chunk_id: str
    doc_name: str
    content: str
    page_number: Optional[int] = None
    section: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_evidence(self, reliability: float = 0.85) -> Evidence:
        provenance = f"{self.doc_name}"
        if self.page_number is not None:
            provenance += f", Page {self.page_number}"
        if self.section:
            provenance += f", Section: {self.section}"
            
        return Evidence(
            evidence_id=generate_id("E-DOC"),
            source_type=ProvenanceType.DOCUMENT_DERIVED,
            source_reference=provenance,
            content=self.content,
            reliability=reliability,
            metadata=self.metadata or {},
        )


def sanitize_untrusted_text(text: str) -> str:
    """
    Sanitizes external document text against prompt injection attempts (Module 38).
    Neutralizes system-prompt override phrases and control chars.
    """
    if not text:
        return ""
    
    # Strip null bytes and non-printable control characters
    cleaned = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)
    
    # Neutralize prompt injection markers like "System Prompt Override", "Ignore previous instructions"
    patterns = [
        r"(?i)ignore\s+(all\s+)?(previous|prior)\s+instructions",
        r"(?i)system\s*prompt\s*override",
        r"(?i)you\s+are\s+now\s+in\s+developer\s+mode",
        r"(?i)<script[\s\S]*?</script>",
    ]
    for pattern in patterns:
        cleaned = re.sub(pattern, "[FILTERED_UNTRUSTED_INSTRUCTION]", cleaned)

    return cleaned.strip()


def chunk_text(
    text: str,
    doc_name: str,
    chunk_size: int = 500,
    chunk_overlap: int = 100,
    page_num: Optional[int] = None,
    section: Optional[str] = None,
) -> List[DocumentChunk]:
    """
    Chunks text into manageable overlapping segments with metadata provenance.
    """
    sanitized = sanitize_untrusted_text(text)
    words = sanitized.split()
    if not words:
        return []

    chunks = []
    start = 0
    step = max(1, chunk_size - chunk_overlap)
    
    while start < len(words):
        chunk_words = words[start : start + chunk_size]
        chunk_str = " ".join(chunk_words)
        chunks.append(
            DocumentChunk(
                chunk_id=generate_id("CHK"),
                doc_name=doc_name,
                content=chunk_str,
                page_number=page_num,
                section=section,
            )
        )
        start += step

    return chunks


class DocumentParser:
    """
    Multi-format document parser supporting PDF, DOCX, TXT, CSV, JSON.
    """

    @staticmethod
    def parse_pdf(file_bytes: bytes, filename: str) -> List[DocumentChunk]:
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        chunks = []
        for idx, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            if page_text.strip():
                page_chunks = chunk_text(page_text, doc_name=filename, page_num=idx + 1)
                chunks.extend(page_chunks)
        return chunks

    @staticmethod
    def parse_docx(file_bytes: bytes, filename: str) -> List[DocumentChunk]:
        doc = docx.Document(io.BytesIO(file_bytes))
        full_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        return chunk_text(full_text, doc_name=filename)

    @staticmethod
    def parse_txt(file_bytes: bytes, filename: str) -> List[DocumentChunk]:
        text = file_bytes.decode("utf-8", errors="replace")
        return chunk_text(text, doc_name=filename)

    @staticmethod
    def parse_json(file_bytes: bytes, filename: str) -> List[DocumentChunk]:
        text = file_bytes.decode("utf-8", errors="replace")
        try:
            data = json.loads(text)
            formatted = json.dumps(data, indent=2)
            return chunk_text(formatted, doc_name=filename)
        except Exception:
            return chunk_text(text, doc_name=filename)

    @classmethod
    def parse_file(cls, file_bytes: bytes, filename: str) -> List[DocumentChunk]:
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".pdf":
            return cls.parse_pdf(file_bytes, filename)
        elif ext in (".docx", ".doc"):
            return cls.parse_docx(file_bytes, filename)
        elif ext in (".json", ".jsonl"):
            return cls.parse_json(file_bytes, filename)
        else:  # Fallback for txt, csv, md, etc.
            return cls.parse_txt(file_bytes, filename)
