from __future__ import annotations

from fastapi import APIRouter, Depends

from app.deps import require_api_key
from app.schemas.forecasting import ForecastRequest, ForecastResponse
from inference import forecasting

router = APIRouter(prefix="/api/v1/forecast", tags=["forecasting"], dependencies=[Depends(require_api_key)])


@router.post("/arrivals", response_model=ForecastResponse)
async def arrivals(payload: ForecastRequest) -> ForecastResponse:
    """Projected monthly tourist arrivals, nationally or for one region."""
    result = forecasting.forecast(year=payload.year, months=payload.months, region=payload.region)
    return ForecastResponse(**result)


@router.get("/regions", response_model=list[str])
async def regions() -> list[str]:
    """Regions the forecast can be broken down by."""
    return forecasting.region_options()
