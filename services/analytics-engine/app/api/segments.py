from __future__ import annotations

from fastapi import APIRouter, Depends

from app.deps import require_api_key
from app.schemas.recommendations import SegmentResponse, TouristProfileIn
from inference import segments

router = APIRouter(prefix="/api/v1/segments", tags=["segments"], dependencies=[Depends(require_api_key)])


@router.post("/assign", response_model=SegmentResponse)
async def assign(payload: TouristProfileIn) -> SegmentResponse:
    """Nearest tourist segment for a profile — used to seed cold-start recommendations."""
    return SegmentResponse(**segments.assign(payload.model_dump()))
