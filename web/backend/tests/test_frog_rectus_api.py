import pytest
from fastapi import HTTPException

from web.backend.app.main import (
    BIOASSAY_EC50_UM,
    _bioassay_response,
    administer_bioassay_dose,
    calculate_bioassay,
    create_bioassay_sample,
    dog_bp_drugs,
    dog_bp_response,
    drugs,
    frog_rectus_dose_response,
    frog_rectus_response,
    rabbit_eye_observation,
)
from web.backend.app.models import BioassayUnknown
from web.backend.app.schemas import (
    BioassayCalculationRequest,
    BioassayDoseRequest,
    BioassaySampleRequest,
    DogDoseRequest,
    FrogDrcRequest,
    RabbitObservationRequest,
    ResponseRequest,
)


class RecordingDB:
    def __init__(self):
        self.items = []
        self.committed = False

    def add(self, item):
        self.items.append(item)

    def flush(self):
        self.items[-1].id = 1

    def commit(self):
        self.committed = True

    def get(self, model, item_id):
        return next((item for item in self.items
                     if isinstance(item, model) and item.id == item_id), None)


def test_drug_list_comes_from_integrated_engine():
    assert {item["name"] for item in drugs()} == {
        "Acetylcholine", "Carbachol", "Nicotine", "Succinylcholine"
    }


def test_ach_response_preserves_model_and_records_observation():
    db = RecordingDB()
    result = frog_rectus_response(
        ResponseRequest(drug="Acetylcholine", concentration=3, unit="µM"), db
    )

    assert result.response_pct == pytest.approx(50)
    assert result.height_mm == pytest.approx(27.5)
    assert len(result.trace) == 100
    assert db.committed
    assert len(db.items) == 2
    assert db.items[-1].concentration_molar == pytest.approx(3e-6)


def test_d_tubocurarine_competitively_reduces_response():
    unblocked = frog_rectus_response(
        ResponseRequest(drug="Acetylcholine", concentration=3, unit="µM"), RecordingDB()
    )
    blocked = frog_rectus_response(
        ResponseRequest(drug="Acetylcholine", concentration=3, unit="µM",
                        antagonist_concentration=1, antagonist_unit="µM"), RecordingDB()
    )

    assert blocked.response_pct < unblocked.response_pct


def test_non_agonist_cannot_be_administered():
    with pytest.raises(HTTPException) as error:
        frog_rectus_response(
            ResponseRequest(drug="d-Tubocurarine", concentration=3, unit="µM"), RecordingDB()
        )
    assert error.value.status_code == 422


def test_dog_bp_uses_desktop_dose_ranges_and_receptor_history():
    metadata = dog_bp_drugs()
    assert set(metadata) == {
        "Epinephrine", "Norepinephrine", "Isoprenaline", "Acetylcholine",
        "Histamine", "Ephedrine", "Phenoxybenzamine", "Propranolol",
        "Atropine", "Saline",
    }
    control = dog_bp_response(DogDoseRequest(
        drug="Epinephrine", dose=2, dose_unit="µg/kg"
    ))
    blocked = dog_bp_response(DogDoseRequest(
        drug="Epinephrine", dose=2, dose_unit="µg/kg",
        prior_drugs=[{"drug": "Phenoxybenzamine", "dose_ug_kg": 2000}],
    ))
    assert len(control["trace"]) == 121
    assert control["response"]
    assert control["explanation"] != blocked["explanation"]


def test_rabbit_eye_tools_return_paired_eye_findings():
    result = rabbit_eye_observation(RabbitObservationRequest(
        drug="Atropine (1%)", drug_eye="right", tool="torch"
    ))
    assert result["right_eye"] == "absent"
    assert result["left_eye"] == "present"


def test_frog_drc_shifts_right_with_competitive_blocker():
    result = frog_rectus_dose_response(FrogDrcRequest(
        drug="Acetylcholine", antagonist_concentrations_um=[0, 0.1, 1, 10]
    ))
    curves = result["curves"]
    assert len(curves) == 4
    assert curves[0]["points"][10]["response_pct"] > curves[-1]["points"][10]["response_pct"]
    assert curves[0]["points"][-1]["response_pct"] == pytest.approx(100, abs=0.01)


def test_bioassay_stock_stays_hidden_and_uses_source_calibration():
    assert _bioassay_response(BIOASSAY_EC50_UM) == pytest.approx(25.0)
    db = RecordingDB()
    sample = create_bioassay_sample(
        BioassaySampleRequest(stock_value=0.72, stock_unit="µg/mL"), db
    )
    assert "stock_concentration_um" not in sample
    assert "0.72" not in str(sample)
    observation = administer_bioassay_dose(BioassayDoseRequest(
        sample_id=sample["sample_id"], solution="standard",
        input_value=0.72, unit="µg/mL",
    ), db)
    assert observation["response_mm"] == pytest.approx(25.0)
    assert len(observation["trace"]) == 181
    unknown = administer_bioassay_dose(BioassayDoseRequest(
        sample_id=sample["sample_id"], solution="unknown",
        input_value=0.5, unit="× stock",
    ), db)
    assert "stock_concentration" not in str(unknown)


def test_bioassay_interpolation_and_four_point_match_desktop_calculations():
    db = RecordingDB()
    sample = create_bioassay_sample(
        BioassaySampleRequest(stock_value=10, stock_unit="µM"), db
    )
    interpolation_records = [
        {"kind": "standard", "level": level,
         "response_mm": _bioassay_response(level)}
        for level in (1.0, 10.0)
    ] + [{"kind": "unknown", "level": 0.5,
          "response_mm": _bioassay_response(5.0)}]
    interpolation = calculate_bioassay(BioassayCalculationRequest(
        sample_id=sample["sample_id"], method="interpolation",
        records=interpolation_records,
    ), db)
    assert interpolation["estimate_um"] == pytest.approx(10.0, rel=0.03)

    four_point_records = [
        {"kind": "standard", "level": 1.0, "response_mm": 10.0},
        {"kind": "unknown", "level": 0.1, "response_mm": 10.0},
        {"kind": "standard", "level": 10.0, "response_mm": 40.0},
        {"kind": "unknown", "level": 1.0, "response_mm": 40.0},
    ]
    four_point = calculate_bioassay(BioassayCalculationRequest(
        sample_id=sample["sample_id"], method="four point",
        records=four_point_records,
    ), db)
    assert four_point["estimate_um"] == pytest.approx(10.0)
    assert four_point["diagnostics"]["slope_difference_percent"] == pytest.approx(0.0)

