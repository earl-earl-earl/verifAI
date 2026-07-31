from app.core.redis import get_redis
from app.core.config import settings
from app.models.claim import ClaimReport
from uuid import UUID

# Helper for creating key name pattern
def report_key(report_id: UUID) -> str:
    return f"claim_report:{report_id}"

# Sets the report into the Redis db
async def set_report(claim_report: ClaimReport) -> None:
    redis_db = get_redis()
    await redis_db.set(report_key(claim_report.id), claim_report.model_dump_json(), ex=settings.UPSTASH_REDIS_CACHE_TTL)

# Gets reports from Redis
async def get_report(report_id: UUID) -> ClaimReport | None:
    redis_db = get_redis()
    result = await redis_db.get(report_key(report_id))
    if result is None:
        return None
    return ClaimReport.model_validate_json(result)

# Update function for reports
async def update_status(report_id: UUID, **fields):
    report = await get_report(report_id)
    if report:
        updated_report = report.model_copy(update=fields)
        await set_report(updated_report)
        return updated_report
    return None