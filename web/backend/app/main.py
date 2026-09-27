import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from integrated_modules.frog_rectus.simulation.engine import (
    BASELINE_MM,
    DRUG_LIBRARY,
    concentration_to_molar,
    generate_contraction_curve,
    get_agonists,
    response_height_mm,
)
from .db import Base, SessionLocal, engine
from .models import ExperimentSession, Observation
from .schemas import ResponseRequest, ResponseResult, TracePoint


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Computer Assisted Learning API", version="0.1.0", lifespan=lifespan)
cors_origins = [
    origin.strip().rstrip("/")
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/frog-rectus/drugs")
def drugs():
    return [
        {"name": drug.name, "emax_pct": drug.emax, "ec50_molar": drug.ec50,
         "hill_n": drug.hill_n, "color": drug.color,
         "molecular_weight": drug.molecular_weight,
         "material_name": drug.material_name}
        for drug in get_agonists().values()
    ]


@app.post("/api/frog-rectus/response", response_model=ResponseResult)
def frog_rectus_response(payload: ResponseRequest, db: Session = Depends(get_db)):
    drug = DRUG_LIBRARY.get(payload.drug)
    if drug is None or drug.drug_type != "agonist":
        raise HTTPException(status_code=422, detail="Select a supported agonist.")
    antagonist = DRUG_LIBRARY["d-Tubocurarine"]
    try:
        concentration = concentration_to_molar(
            payload.concentration, payload.unit, drug.molecular_weight
        )
        antagonist_concentration = (
            concentration_to_molar(payload.antagonist_concentration,
                                    payload.antagonist_unit)
            if payload.antagonist_concentration > 0 else 0.0
        )
        response = drug.mean_response(
            concentration, antagonist_conc=antagonist_concentration,
            antagonist_kb=antagonist.kb,
            antagonist_effective=antagonist_concentration > 0,
        )
    except (ValueError, OverflowError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    height = BASELINE_MM + response_height_mm(response)
    trace = [TracePoint(time=t, height_mm=y) for t, y in generate_contraction_curve(response)]
    session = ExperimentSession(module="frog_rectus")
    db.add(session)
    db.flush()
    db.add(Observation(session_id=session.id, drug=drug.name,
                       concentration_molar=concentration, response_pct=response,
                       peak_height_mm=height))
    db.commit()
    return ResponseResult(drug=drug.name, concentration_molar=concentration,
                          response_pct=response, height_mm=height, trace=trace)
