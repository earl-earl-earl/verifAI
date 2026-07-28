from app.core.database import get_database
from app.models.claim import ClaimReport
from uuid import UUID
from datetime import datetime, timezone

COLLECTION_NAME = "claims"

async def insert(claim_report: ClaimReport):
    db = get_database()
    await db[COLLECTION_NAME].insert_one(claim_report.model_dump(mode="json"))

async def find_by_id(report_id: UUID):
    db = get_database()
    result = await db[COLLECTION_NAME].find_one({"id": str(report_id)})
    if result:
        return ClaimReport(**result)
    return None

async def update(report_id: UUID, fields: dict):
    db = get_database()
    fields["updated_at"] = datetime.now(timezone.utc)
    await db[COLLECTION_NAME].update_one({"id": str(report_id)}, {"$set": fields})

