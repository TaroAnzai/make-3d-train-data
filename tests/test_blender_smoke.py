import json
import shutil

import pytest

from make_3d_train_data.config import load_config
from make_3d_train_data.dataset_builder import build_dataset


@pytest.mark.blender
@pytest.mark.skipif(shutil.which("blender") is None,reason="Blender executable is not installed")
def test_fixed_render(tmp_path):
    cfg = load_config("configs/fixed_sample.yaml")
    cfg["output"].update(root=str(tmp_path), image_width=320, image_height=180)
    cfg["blender"]["samples"] = 8
    root = build_dataset(cfg)
    assert (root / "images/000001.jpg").stat().st_size > 0
    coco = json.loads((root / "annotations/instances.json").read_text())
    assert [item["category_id"] for item in coco["annotations"]] == [1, 28, 36]
    assert len((root / "annotations/yolo/000001.txt").read_text().splitlines()) == 3
