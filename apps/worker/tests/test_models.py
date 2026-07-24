import json
from pathlib import Path
import pytest
from product_twin.models import PackagingSpec
FIX=Path(__file__).parents[3]/'packages/test-fixtures/round-dropper/spec.json'
def data(): return json.loads(FIX.read_text())
def test_fixture_valid(): assert PackagingSpec.model_validate(data()).schema_version=='1.0.0'
@pytest.mark.parametrize('field,value',[('heightMm',-1),('bodyDiameterMm',0),('fillPercent',101)])
def test_invalid_values(field,value):
    d=data()
    if field=='fillPercent': d['liquid'][field]=value
    else:d['dimensions'][field]=value
    with pytest.raises(ValueError): PackagingSpec.model_validate(d)
def test_invalid_color():
    d=data(); d['body']['colorHex']='beige'
    with pytest.raises(ValueError): PackagingSpec.model_validate(d)
