from __future__ import annotations

from pydantic import BaseModel, Field

from .recommendations import TouristProfileIn


class GuideRankRequestTourist(TouristProfileIn):
    region: str | None = Field(None, examples=["Everest/Khumbu"])
    language: str | None = Field(None, examples=["English"])
    experience_level: str | None = Field(None, examples=["First-time"])
    travel_style: str | None = Field(None, examples=["Solo"])
    age: float | None = Field(None, ge=0, le=120, examples=[32])


class GuideCandidate(BaseModel):
    guide_id: str | None = None
    certification: str = Field(..., examples=["IFMGA Mountain Guide"])
    average_rating: float = Field(0, ge=0, le=5)
    regions_covered: str | None = None
    languages_spoken: str | None = None
    # Optional credential fields — the ranker uses them when the caller has them.
    years_experience: float | None = Field(None, ge=0)
    total_trips_completed: int | None = Field(None, ge=0)
    verification_status: str | None = Field(None, examples=["Verified"])


class GuideRankRequest(BaseModel):
    tourist: GuideRankRequestTourist
    candidates: list[GuideCandidate]


class RankedGuide(GuideCandidate):
    score: float
    components: dict[str, float]
    predicted_rating: float | None = None


class GuideRankResponse(BaseModel):
    model_version: str
    items: list[RankedGuide]
