import json
from pathlib import Path
from product_twin.blender.archetypes.round_dropper import rotational_profile
FIX=Path(__file__).parents[3]/'packages/test-fixtures/round-dropper/spec.json'
def test_profile_is_monotonic_and_bounded():
    p=rotational_profile(json.loads(FIX.read_text())); assert p[0][0]==0; assert all(z2>=z1 for (z1,_),(z2,_) in zip(p,p[1:])); assert max(r for _,r in p)<=21
