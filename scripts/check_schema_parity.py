from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'apps/worker'))
from product_twin.models import PackagingSpec
fixture=json.loads((ROOT/'packages/test-fixtures/round-dropper/spec.json').read_text())
PackagingSpec.model_validate(fixture)
schema=json.loads((ROOT/'packages/packaging-schema/packaging-spec.schema.json').read_text())
assert schema['properties']['schemaVersion']['const']==PackagingSpec.model_fields['schema_version'].default
assert set(schema['properties']['body']['properties']['material']['enum'])=={'clear-glass','frosted-glass','glossy-plastic','matte-plastic'}
print('schema parity: ok')
