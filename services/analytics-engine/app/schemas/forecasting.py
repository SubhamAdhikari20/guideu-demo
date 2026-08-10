from __future__ import annotations

from pydantic import BaseModel, Field


class ForecastRequest(BaseModel):
    year: int | None = Field(None, ge=2020, le=2100, examples=[2025])
    months: list[int] | None = Field(None, examples=[[9, 10, 11]])
    region: str | None = Field(None, examples=["Everest/Khumbu"])


class ForecastPoint(BaseModel):
    year: int
    month: int
    predicted_arrivals: int
    lower_estimate: int
    upper_estimate: int


class ForecastResponse(BaseModel):
    model_version: str
    year: int | None
    region: str | None = None
    expected_error_pct: float | None = None
    peak_month: int | None = None
    items: list[ForecastPoint]
    # Last year present in the training series, and how far past it this request
    # reaches. `reliable` is false once the trend is being extrapolated beyond
    # what three years of recovery data can support.
    last_observed_year: int | None = None
    horizon_years: int | None = None
    reliable: bool = True
    note: str | None = None
