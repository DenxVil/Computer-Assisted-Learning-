from pydantic import BaseModel, Field


class ResponseRequest(BaseModel):
    drug: str
    concentration: float = Field(gt=0, allow_inf_nan=False)
    unit: str
    antagonist_concentration: float = Field(default=0, ge=0, allow_inf_nan=False)
    antagonist_unit: str = "M"


class TracePoint(BaseModel):
    time: float
    height_mm: float


class ResponseResult(BaseModel):
    drug: str
    concentration_molar: float
    response_pct: float
    height_mm: float
    trace: list[TracePoint]
