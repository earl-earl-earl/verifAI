from enum import Enum
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime, timezone

# Verdicts
class Verdict(str, Enum):
    TRUE = "true"
    FALSE = "false"
    MISLEADING = "misleading"
    UNVERIFIABLE = "unverifiable"

# Claim Status
class ClaimStatus(str, Enum):
    PENDING = "pending"
    SCRAPING = "scraping"
    ANALYZING = "analyzing"
    DONE = "done"
    FAILED = "failed"

# Base claim model
# For repetitive fields
class ClaimBase(BaseModel):
    claim: str = Field(..., min_length=10, max_length=1000)

# Source model
# Represents one piece of scraped evidence
class Source(BaseModel):
    url: HttpUrl
    title: str
    snippet: str
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Submit Claim model
# What client sends when submitting a claim
class SubmitClaimRequest(ClaimBase):
    pass

# Claim Report model
# Central data model
class ClaimReport(ClaimBase):
    id: UUID = Field(default_factory=uuid4)
    status: ClaimStatus = ClaimStatus.PENDING
    verdict: Verdict | None = None
    confidence: float | None = Field(
        default=None,
        ge=0,
        le=1
    )
    explanation: str | None = None
    sources: list[Source] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Submit Claim Response model
# What the API returns after `POST /claims`
class SubmitClaimResponse(BaseModel):
    id: UUID
    status: ClaimStatus
    message: str