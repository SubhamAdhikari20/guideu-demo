from __future__ import annotations

from pydantic import BaseModel, Field


class TouristProfileIn(BaseModel):
    pref_adventure_score: float = Field(0.5, ge=0, le=1)
    pref_culture_score: float = Field(0.5, ge=0, le=1)
    pref_nature_score: float = Field(0.5, ge=0, le=1)
    risk_tolerance: float = Field(0.5, ge=0, le=1)
    price_sensitivity: float = Field(0.5, ge=0, le=1)
    budget_band: str | None = Field(None, examples=["Mid-range"])
    fitness_level: str | None = Field(None, examples=["Good"])


class RecommendRequest(BaseModel):
    tourist: TouristProfileIn
    season: str | None = Field(None, examples=["Autumn"])
    top_k: int = Field(5, ge=1, le=50)


class RouteRecommendation(BaseModel):
    route_id: str
    route_name: str
    region: str
    difficulty: str
    score: float
    components: dict[str, float]
    # Plain-language reasons taken from the ranker's own feature contributions.
    why: list[str] = Field(default_factory=list)


class RecommendResponse(BaseModel):
    model_version: str
    items: list[RouteRecommendation]


class SegmentSummary(BaseModel):
    segment_id: int
    name: str | None = None
    size: int | None = None


class SegmentResponse(BaseModel):
    model_version: str
    segment_id: int | None
    name: str | None
    size: int | None = None
    centroid: dict[str, float] = Field(default_factory=dict)
    segments: list[SegmentSummary] = Field(default_factory=list)
