import shutil,pytest
from make_3d_train_data.config import load_config
from make_3d_train_data.dataset_builder import build_dataset
@pytest.mark.blender
@pytest.mark.skipif(shutil.which("blender") is None,reason="Blender executable is not installed")
def test_fixed_render(tmp_path):
    cfg=load_config("configs/fixed_sample.yaml"); cfg["output"]["root"]=str(tmp_path); root=build_dataset(cfg); assert (root/"images/000001.jpg").exists() and (root/"labels/instances.json").exists()
