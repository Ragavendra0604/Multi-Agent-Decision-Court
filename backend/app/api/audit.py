"""
Audit Trail REST Endpoints.
Implements Module 37 (Audit Trail).
"""

import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.db_models import AuditLogDB

router = APIRouter(prefix="/api/audit", tags=["Audit"])


@router.get("/{case_id}")
async def get_case_audit_logs(case_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AuditLogDB).where(AuditLogDB.case_id == case_id).order_by(AuditLogDB.timestamp.asc())
    )
    logs = result.scalars().all()
    return [
        {
            "id": l.id,
            "case_id": l.case_id,
            "event_type": l.event_type,
            "actor": l.actor,
            "details": json.loads(l.details or "{}"),
            "timestamp": l.timestamp.isoformat(),
        }
        for l in logs
    ]
