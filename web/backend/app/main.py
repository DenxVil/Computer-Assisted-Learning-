import os
import math
import secrets
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import numpy as np

from experiments.dog_bp_model import DOSE_METADATA, simulate_response, validate_dose

from integrated_modules.frog_rectus.simulation.engine import (
    BASELINE_MM,
    DRUG_LIBRARY,
    concentration_to_molar,
    generate_contraction_curve,
    get_agonists,
    get_antagonists,
    generate_dose_series,
    response_height_mm,
    generate_wash_curve,
)
from .db import Base, SessionLocal, engine
from .models import BioassayUnknown, ExperimentSession, Observation
from .schemas import (BioassayCalculationRequest, BioassayDoseRequest,
                      BioassaySampleRequest, DogDoseRequest,
                      FrogDrcRequest, FrogWashRequest,
                      RabbitObservationRequest, ResponseRequest,
                      ResponseResult, TracePoint)


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


RABBIT_EYE_DRUGS = {
    "Atropine (1%)": {"class": "Anticholinergic (M3 antagonist)", "pupil_size": "mydriasis", "pupil_mm": 9.0, "light_reflex": "absent", "corneal_reflex": "present", "conjunctiva": "no significant change", "tone": "increased IOP (~25–30 mmHg)", "mechanism": "M3 antagonist relaxes sphincter pupillae, producing mydriasis and cycloplegia; light reflex is abolished.", "onset": "20–30 min", "duration": "7–10 days"},
    "Lignocaine (4%)": {"class": "Local anaesthetic", "pupil_size": "normal", "pupil_mm": 6.0, "light_reflex": "present", "corneal_reflex": "absent", "conjunctiva": "no significant change", "tone": "No change in IOP", "mechanism": "Sodium-channel block abolishes corneal sensation without an autonomic pupil effect.", "onset": "1–5 min", "duration": "30–60 min"},
    "Cocaine (4%)": {"class": "Noradrenaline reuptake inhibitor + local anaesthetic", "pupil_size": "mydriasis", "pupil_mm": 8.5, "light_reflex": "present", "corneal_reflex": "absent", "conjunctiva": "blanched — vasoconstriction", "tone": "No significant change", "mechanism": "Noradrenaline reuptake inhibition produces mydriasis with preserved light reflex; local anaesthesia abolishes corneal reflex and vasoconstriction blanches conjunctiva.", "onset": "5–10 min", "duration": "1–2 hours"},
    "Ephedrine (1%)": {"class": "Mixed sympathomimetic", "pupil_size": "mydriasis", "pupil_mm": 8.0, "light_reflex": "present", "corneal_reflex": "present", "conjunctiva": "mild blanching — vasoconstriction", "tone": "No significant change", "mechanism": "Noradrenaline release and direct α₁ action produce mydriasis; reflexes remain intact.", "onset": "10–20 min", "duration": "3–6 hours"},
    "Pilocarpine (1%)": {"class": "Cholinomimetic (M3 agonist)", "pupil_size": "miosis", "pupil_mm": 3.0, "light_reflex": "present", "corneal_reflex": "present", "conjunctiva": "congested — vasodilation", "tone": "Decreased IOP (~10–15 mmHg)", "mechanism": "M3 stimulation contracts sphincter pupillae (miosis) and opens the trabecular meshwork, lowering IOP.", "onset": "10–20 min", "duration": "4–8 hours"},
}


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


@app.post("/api/frog-rectus/dose-response")
def frog_rectus_dose_response(payload: FrogDrcRequest):
    drug = DRUG_LIBRARY.get(payload.drug)
    if drug is None or drug.drug_type != "agonist":
        raise HTTPException(status_code=422, detail="Select a supported agonist.")
    concentrations = payload.antagonist_concentrations_um
    if not concentrations or len(concentrations) > 6 or any(
        not math.isfinite(float(value)) or float(value) < 0 for value in concentrations
    ):
        raise HTTPException(status_code=422, detail="Use one to six finite non-negative antagonist concentrations.")
    antagonist = DRUG_LIBRARY["d-Tubocurarine"]
    doses = generate_dose_series(1e-8, 1e-3, points_per_log=3)
    curves = []
    for antagonist_um in concentrations:
        antagonist_molar = float(antagonist_um) * 1e-6
        response_curve = [drug.mean_response(
            dose, antagonist_conc=antagonist_molar,
            antagonist_kb=antagonist.kb,
            antagonist_effective=antagonist_molar > 0,
        ) for dose in doses]
        curves.append({
            "antagonist_um": float(antagonist_um),
            "points": [{"concentration_molar": dose, "response_pct": response,
                        "height_mm": BASELINE_MM + response_height_mm(response)}
                       for dose, response in zip(doses, response_curve)],
        })
    return {"drug": drug.name, "ec50_molar": drug.ec50,
            "emax_pct": drug.emax, "hill_n": drug.hill_n,
            "antagonist_kb_molar": antagonist.kb,
            "curves": curves}


@app.post("/api/frog-rectus/wash")
def frog_rectus_wash(payload: FrogWashRequest):
    return {"trace": [TracePoint(time=t, height_mm=y)
                      for t, y in generate_wash_curve(payload.current_height_mm)]}


@app.get("/api/dog-bp/drugs")
def dog_bp_drugs():
    """Return the original teaching ranges, display units and dose presets."""
    return {
        name: {
            **metadata,
            "min_display": metadata["min_ug_kg"] / metadata["display_factor"],
            "max_display": metadata["max_ug_kg"] / metadata["display_factor"],
            "default_display": metadata["default_ug_kg"] / metadata["display_factor"],
            "presets_display": [dose / metadata["display_factor"]
                                for dose in metadata["presets_ug_kg"]],
        }
        for name, metadata in DOSE_METADATA.items()
    }


@app.post("/api/dog-bp/response")
def dog_bp_response(payload: DogDoseRequest):
    """Use the desktop Dog BP model for a 60-second injection trace."""
    metadata = DOSE_METADATA.get(payload.drug)
    if metadata is None:
        raise HTTPException(status_code=422, detail="Select a supported drug.")
    if payload.dose_unit != metadata["display_unit"]:
        raise HTTPException(status_code=422, detail="Dose unit does not match the selected drug.")
    dose_ug_kg = payload.dose * metadata["display_factor"]
    valid, message = validate_dose(payload.drug, dose_ug_kg)
    if not valid:
        raise HTTPException(status_code=422, detail=message)
    time = np.linspace(0.0, 60.0, 121)
    result = simulate_response(payload.drug, dose_ug_kg, time, prior_drugs=payload.prior_drugs)
    baseline = result["baseline"]
    map_delta = result["map"] - baseline["map"]
    hr_delta = result["hr"] - baseline["hr"]
    map_rise, map_fall = max(0.0, float(np.max(map_delta))), min(0.0, float(np.min(map_delta)))
    hr_rise, hr_fall = max(0.0, float(np.max(hr_delta))), min(0.0, float(np.min(hr_delta)))
    if map_rise > 2 and map_fall < -2:
        bp_pattern = "MAP ↑ then ↓"
    elif map_rise > 2:
        bp_pattern = "MAP ↑"
    elif map_fall < -2:
        bp_pattern = "MAP ↓"
    else:
        bp_pattern = "MAP ↔"
    if hr_rise > 2 and hr_fall < -2:
        hr_pattern = "HR ↑ then ↓"
    elif hr_rise > 2:
        hr_pattern = "HR ↑"
    elif hr_fall < -2:
        hr_pattern = "HR ↓"
    else:
        hr_pattern = "HR ↔"
    return {
        "drug": payload.drug,
        "dose_ug_kg": dose_ug_kg,
        "dose_display": f"{payload.dose:g} {metadata['display_unit']}",
        "explanation": result["explanation"],
        "baseline": baseline,
        "map_rise": map_rise, "map_fall": map_fall,
        "hr_rise": hr_rise, "hr_fall": hr_fall,
        "response": f"{bp_pattern}; {hr_pattern}",
        "blockades": result["blockades"],
        "trace": [
            {"time": float(t), "sbp": float(result["sbp"][i]),
             "dbp": float(result["dbp"][i]), "map": float(result["map"][i]),
             "hr": float(result["hr"][i])}
            for i, t in enumerate(time)
        ],
    }


@app.get("/api/rabbit-eye/drugs")
def rabbit_eye_drugs():
    return RABBIT_EYE_DRUGS


@app.post("/api/rabbit-eye/observation")
def rabbit_eye_observation(payload: RabbitObservationRequest):
    drug = RABBIT_EYE_DRUGS.get(payload.drug)
    if drug is None:
        raise HTTPException(status_code=422, detail="Select a supported eye drug.")
    if payload.drug_eye not in {"left", "right"}:
        raise HTTPException(status_code=422, detail="Choose the drug-treated eye.")
    key_by_tool = {
        "ruler": ("Pupil", "pupil_size", "pupil_mm"),
        "torch": ("Light reflex", "light_reflex", None),
        "swab": ("Corneal reflex", "corneal_reflex", None),
        "conjunctiva": ("Conjunctiva", "conjunctiva", None),
        "tone": ("Ocular tone", "tone", None),
    }
    config = key_by_tool.get(payload.tool)
    if config is None:
        raise HTTPException(status_code=422, detail="Choose one of the practical tools.")
    label, key, numeric_key = config
    drug_value = drug[key]
    if numeric_key:
        drug_value = f"{drug_value} ({drug[numeric_key]:.1f} mm)"
    result = {"parameter": label, "left_eye": "Normal saline control", "right_eye": "Normal saline control"}
    result[f"{payload.drug_eye}_eye"] = drug_value
    result[f"{'right' if payload.drug_eye == 'left' else 'left'}_eye"] = (
        "normal (6.0 mm)" if payload.tool == "ruler" else
        "present" if payload.tool in {"torch", "swab"} else
        "normal pink vasculature" if payload.tool == "conjunctiva" else
        "normal IOP (~15–20 mmHg)"
    )
    return {**result, "mechanism": drug["mechanism"], "onset": drug["onset"], "duration": drug["duration"]}


BIOASSAY_UNITS = {
    "M": 1e6, "mM": 1e3, "µM": 1.0, "μM": 1.0, "uM": 1.0,
    "nM": 1e-3, "mg/mL": 1e6 / 181.66,
    "µg/mL": 1e3 / 181.66, "ug/mL": 1e3 / 181.66,
    "ng/mL": 1.0 / 181.66, "g/L": 1e6 / 181.66,
}
BIOASSAY_EMAX_MM = 50.0
BIOASSAY_EC50_UG_ML = 0.72
BIOASSAY_EC50_UM = BIOASSAY_EC50_UG_ML * 1000.0 / 181.66
BIOASSAY_HILL = 1.35


def _bioassay_response(concentration_um: float) -> float:
    """The same Hill calibration used by experiments/bioassay.py."""
    if concentration_um <= 0:
        return 0.0
    log_ratio = BIOASSAY_HILL * (
        math.log(BIOASSAY_EC50_UM) - math.log(concentration_um)
    )
    if log_ratio >= 709:
        return 0.0
    if log_ratio <= -709:
        return BIOASSAY_EMAX_MM
    return BIOASSAY_EMAX_MM / (1.0 + math.exp(log_ratio))


def _bioassay_stock(db: Session, sample_id: str):
    stock = db.get(BioassayUnknown, sample_id)
    if stock is None:
        raise HTTPException(status_code=404, detail="Unknown sample not found. Prepare a new sample.")
    return stock


@app.post("/api/bioassay/samples")
def create_bioassay_sample(payload: BioassaySampleRequest, db: Session = Depends(get_db)):
    """Create a hidden teacher-stock sample; the stock value is not returned."""
    if payload.stock_value is None:
        stock_ug_ml = secrets.choice((0.30, 0.50, 0.65, 1.00, 1.25, 2.00))
        stock_um = stock_ug_ml * 1000.0 / 181.66
    else:
        factor = BIOASSAY_UNITS.get(payload.stock_unit)
        if factor is None:
            raise HTTPException(status_code=422, detail="Unsupported unknown stock concentration unit.")
        stock_um = payload.stock_value * factor
    if not math.isfinite(stock_um) or stock_um <= 0:
        raise HTTPException(status_code=422, detail="Unknown stock must be a positive finite concentration.")
    sample_id = str(uuid.uuid4())
    code = "ACh-" + secrets.token_hex(3).upper()
    db.add(BioassayUnknown(id=sample_id, code=code, stock_concentration_um=stock_um))
    db.commit()
    return {"sample_id": sample_id, "sample_code": code, "configured": True}


@app.post("/api/bioassay/dose")
def administer_bioassay_dose(payload: BioassayDoseRequest, db: Session = Depends(get_db)):
    stock = _bioassay_stock(db, payload.sample_id)
    solution = payload.solution.strip().lower()
    if solution == "standard":
        factor = BIOASSAY_UNITS.get(payload.unit)
        if factor is None:
            raise HTTPException(status_code=422, detail="Unsupported standard concentration unit.")
        effective_um = payload.input_value * factor
        dose_label = f"{payload.input_value:g} {payload.unit} final bath"
        kind = "standard"
        level = effective_um
        display_solution = "Standard ACh"
    elif solution == "unknown":
        try:
            fraction = (payload.input_value / 100.0 if payload.unit == "% stock"
                        else payload.input_value if payload.unit == "× stock" else None)
        except (TypeError, ValueError):
            fraction = None
        if fraction is None or not math.isfinite(fraction) or fraction <= 0:
            raise HTTPException(status_code=422, detail="Use a positive × stock or % stock dilution.")
        effective_um = stock.stock_concentration_um * fraction
        dose_label = f"{payload.input_value:g} {payload.unit}"
        kind = "unknown"
        level = fraction
        display_solution = "Unknown ACh test"
    else:
        raise HTTPException(status_code=422, detail="Choose Standard ACh or Unknown ACh test.")
    response = _bioassay_response(effective_um)
    trace = []
    for frame in range(181):
        time_s = frame * 0.5
        if time_s < 5.0:
            movement = 0.0
        elif time_s < 35.0:
            movement = response * (1.0 - math.exp(-(time_s - 5.0) / 8.0))
        else:
            movement = response * (0.985 + 0.012 * math.sin(time_s / 5.5))
        trace.append({"time": time_s, "height_mm": max(0.0, min(response, movement))})
    return {
        "solution": display_solution, "dose_label": dose_label,
        "kind": kind, "level": level,
        "response_mm": response, "response_pct": response / BIOASSAY_EMAX_MM * 100.0,
        "trace": trace,
        "guidance": ("Response is very low; increase the dose for a useful comparison." if response < 5
                     else "Response is near maximum; use a lower concentration in the middle response range." if response > 45
                     else "Submaximal response recorded. Wash the tissue before the next dose."),
    }


@app.post("/api/bioassay/calculate")
def calculate_bioassay(payload: BioassayCalculationRequest, db: Session = Depends(get_db)):
    stock = _bioassay_stock(db, payload.sample_id)
    method = payload.method.strip().lower()
    standards = []
    tests = []
    for item in payload.records:
        kind = item.get("kind")
        level = float(item.get("level", 0))
        response = float(item.get("response_mm", 0))
        if not math.isfinite(level) or level <= 0 or not math.isfinite(response):
            continue
        if kind == "standard":
            standards.append((level, response))
        elif kind == "unknown":
            tests.append((level, response))
    if method not in {"interpolation", "three point", "four point"}:
        raise HTTPException(status_code=422, detail="Select Interpolation, Three point, or Four point.")
    if len(standards) < 2 or not tests:
        raise HTTPException(status_code=422, detail=(
            "Record two different standard levels and one unknown test fraction."
            if method == "three point" else
            "Record at least two different standards and one unknown test response."
        ))

    def same_level(first, second):
        return math.isclose(first, second, rel_tol=1e-9, abs_tol=1e-12)

    def group_means(records):
        levels, grouped = [], []
        for level, response in records:
            index = next((i for i, old in enumerate(levels) if same_level(level, old)), None)
            if index is None:
                levels.append(level)
                grouped.append([response])
            else:
                grouped[index].append(response)
        return [(level, sum(values) / len(values))
                for level, values in zip(levels, grouped)]

    def latest_distinct_points(records):
        selected = []
        for level, _response in reversed(records):
            if not any(same_level(level, existing) for existing in selected):
                selected.append(level)
            if len(selected) == 2:
                break
        if len(selected) < 2:
            return []
        return group_means([(level, response) for level, response in records
                            if any(same_level(level, chosen) for chosen in selected)])

    standard_points = group_means(standards)
    if method == "four point":
        standard_points = latest_distinct_points(standards)
        test_points = latest_distinct_points(tests)
        if len(standard_points) < 2 or len(test_points) < 2:
            raise HTTPException(status_code=422, detail=(
                "Record two different standard levels and two different unknown test fractions."
            ))
        sx = [math.log10(point[0]) for point in standard_points]
        sy = [point[1] for point in standard_points]
        tx = [math.log10(point[0]) for point in test_points]
        ty = [point[1] for point in test_points]
        if sx[0] == sx[1] or tx[0] == tx[1]:
            raise HTTPException(status_code=422, detail="Use two different levels for both standard and test.")
        standard_slope = (sy[1] - sy[0]) / (sx[1] - sx[0])
        test_slope = (ty[1] - ty[0]) / (tx[1] - tx[0])
        if standard_slope <= 0 or test_slope <= 0:
            raise HTTPException(status_code=422, detail="Responses must increase with concentration and test fraction.")
        sx_mean, tx_mean = sum(sx) / 2, sum(tx) / 2
        sy_mean, ty_mean = sum(sy) / 2, sum(ty) / 2
        denominator = sum((value - sx_mean) ** 2 for value in sx)
        denominator += sum((value - tx_mean) ** 2 for value in tx)
        numerator = sum((x - sx_mean) * (y - sy_mean) for x, y in zip(sx, sy))
        numerator += sum((x - tx_mean) * (y - ty_mean) for x, y in zip(tx, ty))
        if denominator <= 0:
            raise HTTPException(status_code=422, detail="The selected levels do not permit a slope calculation.")
        common_slope = numerator / denominator
        if common_slope <= 0:
            raise HTTPException(status_code=422, detail="A positive common slope could not be calculated.")
        standard_intercept = sy_mean - common_slope * sx_mean
        test_intercept = ty_mean - common_slope * tx_mean
        estimate_um = 10 ** ((test_intercept - standard_intercept) / common_slope)
        slope_difference = abs(standard_slope - test_slope) / max(
            abs((standard_slope + test_slope) / 2), 1e-12) * 100
        diagnostics = {
            "method": "Four point", "standard_slope": standard_slope,
            "test_slope": test_slope, "common_slope": common_slope,
            "slope_difference_percent": slope_difference,
            "standard_points": standard_points, "test_points": test_points,
            "caution": ("Slopes differ by more than 30 percent; repeat with middle range responses."
                        if slope_difference > 30 else None),
        }
    else:
        if method == "three point":
            standard_points = latest_distinct_points(standards)
            if len(standard_points) < 2:
                raise HTTPException(status_code=422, detail="Record two different standard levels and one unknown test fraction.")
        latest_fraction = tests[-1][0]
        test_response = sum(response for level, response in tests
                            if same_level(level, latest_fraction)) / sum(
                                1 for level, _response in tests if same_level(level, latest_fraction))
        if not math.isfinite(latest_fraction) or latest_fraction <= 0:
            raise HTTPException(status_code=422, detail="The unknown test fraction must be positive.")
        response_sorted = sorted(standard_points, key=lambda point: point[1])
        bracket = next(((lower, upper) for lower, upper in zip(response_sorted[:-1], response_sorted[1:])
                        if lower[0] > 0 and upper[0] > 0 and lower[1] <= test_response <= upper[1]
                        and upper[1] > lower[1]), None)
        if bracket is None:
            raise HTTPException(status_code=422, detail="The unknown response must lie between two standard responses.")
        lower, upper = bracket
        fraction = (test_response - lower[1]) / (upper[1] - lower[1])
        estimate_um = 10 ** (math.log10(lower[0]) + fraction *
                              (math.log10(upper[0]) - math.log10(lower[0]))) / latest_fraction
        diagnostics = {
            "method": "Three point" if method == "three point" else "Interpolation",
            "standard_points": standard_points,
            "test_points": [(latest_fraction, test_response)],
            "lower": lower, "upper": upper,
        }
    if not math.isfinite(estimate_um) or estimate_um <= 0:
        raise HTTPException(status_code=422, detail="The observations did not give a valid positive concentration.")
    return {"estimate_um":estimate_um,"estimate_ug_ml":estimate_um*181.66/1000.0,"diagnostics":diagnostics}


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

