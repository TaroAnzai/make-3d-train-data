from unittest.mock import patch

from PIL import Image

from make_3d_train_data.config import load_config
from make_3d_train_data.dataset_builder import build_dataset


def test_generate_shows_completed_images_in_progress_bar(tmp_path, capsys):
    cfg = load_config("configs/fixed_sample.yaml")
    cfg["output"].update(root=str(tmp_path), count=2)

    def render_stub(scene, config, scene_path, result_path, image_path, blender_bin):
        Image.new("RGB", (8, 8)).save(image_path)
        return {"annotations": []}

    with patch("make_3d_train_data.dataset_builder.render_scene", side_effect=render_stub):
        root = build_dataset(cfg)

    progress = capsys.readouterr().err
    assert "100%" in progress
    assert "2/2" in progress
    assert (root / "images/000001.jpg").is_file()
    assert (root / "images/000002.jpg").is_file()
    assert len((root / "meta/manifest.jsonl").read_text().splitlines()) == 2
