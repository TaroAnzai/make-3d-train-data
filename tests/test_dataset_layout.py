import hashlib
import json
import random
from datetime import datetime
from unittest.mock import patch

import yaml
from PIL import Image

from make_3d_train_data.config import load_config
from make_3d_train_data.dataset_builder import build_dataset


def _render(scene, config, scene_path, result_path, image_path, blender_bin):
    rng = random.Random(scene.seed)
    image = Image.frombytes("RGB", (16, 16), rng.randbytes(16 * 16 * 3))
    image.save(image_path)
    return {"annotations": []}


def test_numbered_layout_and_unique_images_across_runs(tmp_path):
    cfg = load_config("configs/default_random.yaml")
    cfg["output"].update(root=str(tmp_path), count=3)
    (tmp_path / "default_random-07-40").mkdir()
    (tmp_path / "other-99-100").mkdir()

    with patch("make_3d_train_data.dataset_builder.render_scene", side_effect=_render):
        first = build_dataset(cfg)
        second = build_dataset(cfg)

    assert first.name == "default_random-08-3"
    assert second.name == "default_random-09-3"
    for root, number in ((first, 8), (second, 9)):
        descriptor = yaml.safe_load((root / "dataset.yaml").read_text())
        assert descriptor == {"name": f"cg_{datetime.now().astimezone():%Y%m%d}_{number:03d}", "format": "coco", "class_schema": "canonical37"}
        assert len(list((root / "images").glob("*.jpg"))) == 3
        assert json.loads((root / "annotations/instances.json").read_text())["images"]
        assert (root / "meta/used_config.yaml").is_file()
    hashes = [hashlib.sha256(path.read_bytes()).digest() for root in (first, second) for path in sorted((root / "images").glob("*.jpg"))]
    assert len(set(hashes)) == 6
    assert cfg["general"]["seed"] == 12345


def test_duplicate_render_is_retried(tmp_path):
    cfg = load_config("configs/default_random.yaml")
    cfg["output"].update(root=str(tmp_path), count=2)
    calls = []

    def render(scene, config, scene_path, result_path, image_path, blender_bin):
        calls.append(scene.seed)
        if len(calls) <= 2:
            Image.new("RGB", (8, 8), "black").save(image_path)
        else:
            _render(scene, config, scene_path, result_path, image_path, blender_bin)
        return {"annotations": []}

    with patch("make_3d_train_data.dataset_builder.render_scene", side_effect=render), patch(
        "make_3d_train_data.dataset_builder._postprocess"
    ):
        root = build_dataset(cfg)
    assert len(calls) == 3
    assert len({path.read_bytes() for path in (root / "images").glob("*.jpg")}) == 2
