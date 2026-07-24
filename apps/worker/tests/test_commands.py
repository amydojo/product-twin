from pathlib import Path
import pytest
from product_twin.commands import blender_command,safe_child
def test_command_is_argument_list(): assert blender_command('blender',Path('/x/spec.json'),Path('/x/out'),Path('/x/generate.py'))[0]=='blender'
def test_path_traversal_rejected(tmp_path):
    with pytest.raises(ValueError): safe_child(tmp_path,tmp_path/'../escape')
