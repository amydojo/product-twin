from pathlib import Path
from PIL import Image
from product_twin.service import render_fixture
FIX=Path(__file__).parents[3]/'packages/test-fixtures/round-dropper/spec.json'
def test_fixture_render_structural(tmp_path):
    manifest=render_fixture(FIX,tmp_path,allow_fallback=True)
    for name in ['front.png','three-quarter.png','ecommerce.png','product.glb','manifest.json']: assert (tmp_path/name).stat().st_size>10
    assert Image.open(tmp_path/'front.png').mode=='RGBA'; assert Image.open(tmp_path/'ecommerce.png').getpixel((0,0))[:3]==(255,255,255)
    assert 'BODY' in manifest['generatedObjectNames']
