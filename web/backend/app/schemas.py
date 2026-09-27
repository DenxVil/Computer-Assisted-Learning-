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


class DogDoseRequest(BaseModel):
    drug: str
    dose: float = Field(gt=0, allow_inf_nan=False)
    dose_unit: str
    prior_drugs: list[dict] = Field(default_factory=list)


class RabbitObservationRequest(BaseModel):
    drug: str
    drug_eye: str
    tool: str


class BioassaySampleRequest(BaseModel):
    stock_value: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    stock_unit: str = "µg/mL"


class BioassayDoseRequest(BaseModel):
    sample_id: str
    solution: str
    input_value: float = Field(gt=0, allow_inf_nan=False)
    unit: str


class BioassayCalculationRequest(BaseModel):
    sample_id: str
    method: str
    records: list[dict]


class FrogDrcRequest(BaseModel):
    drug: str
    antagonist_concentrations_um: list[float] = Field(default_factory=lambda: [0.0])


class FrogWashRequest(BaseModel):
    current_height_mm: float = Field(ge=5, allow_inf_nan=False)

