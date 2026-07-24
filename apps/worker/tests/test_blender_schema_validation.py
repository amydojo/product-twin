import json
from pathlib import Path

import pytest

from product_twin.blender.schema_validation import validate_spec

FIXTURE = Path(__file__).parents[3] / "packages/test-fixtures/round-dropper/spec.json"


def test_blender_dependency_free_validation_accepts_fixture() -> None:
    assert validate_spec(json.loads(FIXTURE.read_text()))["archetype"] == "round-dropper"


def test_blender_dependency_free_validation_rejects_impossible_neck() -> None:
    spec = json.loads(FIXTURE.read_text())
    spec["dimensions"]["neckDiameterMm"] = spec["dimensions"]["bodyDiameterMm"]
    with pytest.raises(ValueError, match="narrower"):
        validate_spec(spec)
