"""
Database Models for Multi-Agent Decision Court.
Implements Module 39 (Database Design), Module 1 (Auth & Users), Module 2 (Case Management),
Module 35 (Versioning), Module 36 (Human Review), and Module 37 (Audit Trail).
"""

from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class UserDB(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    role = Column(String(64), default="ANALYST", nullable=False)
    organization_id = Column(String(64), default="default_org", index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class CaseDB(Base):
    __tablename__ = "cases"

    case_id = Column(String(64), primary_key=True, index=True)
    title = Column(String(512), nullable=False)
    problem = Column(Text, nullable=False)
    proposed_decision = Column(Text, nullable=False)
    context = Column(Text, nullable=True)
    initial_analysis = Column(Text, nullable=True)
    reasoning = Column(Text, nullable=True)
    state = Column(String(64), default="DRAFT", index=True)
    version = Column(Integer, default=1)
    organization_id = Column(String(64), default="default_org", index=True)
    created_by = Column(String(64), default="anonymous")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Store complete structured payload as JSON for flexible document-graph querying
    data_json = Column(Text, default="{}")


class CaseVersionDB(Base):
    __tablename__ = "case_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(64), ForeignKey("cases.case_id"), index=True)
    version = Column(Integer, nullable=False)
    snapshot_json = Column(Text, nullable=False)
    change_summary = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class VerdictDB(Base):
    __tablename__ = "verdicts"

    verdict_id = Column(String(64), primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("cases.case_id"), index=True)
    version = Column(Integer, default=1)
    verdict = Column(String(64), nullable=False)
    confidence = Column(Float, default=0.5)
    correctness_status = Column(String(64), nullable=True)
    justification_status = Column(String(64), nullable=True)
    summary_rationale = Column(Text, nullable=False)
    verdict_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class HumanReviewDB(Base):
    __tablename__ = "human_reviews"

    review_id = Column(String(64), primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("cases.case_id"), index=True)
    reviewer_id = Column(String(64), nullable=False)
    action = Column(String(64), nullable=False)  # ACCEPT, MODIFY, REJECT
    notes = Column(Text, nullable=False)
    override_reason = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AuditLogDB(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(64), index=True)
    event_type = Column(String(128), nullable=False)
    actor = Column(String(128), default="system")
    details = Column(Text, default="{}")
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
