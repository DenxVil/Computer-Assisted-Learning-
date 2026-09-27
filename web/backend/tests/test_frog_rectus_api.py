import pytest
from fastapi import HTTPException

from web.backend.app.main import drugs, frog_rectus_response
from web.backend.app.schemas import ResponseRequest


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
