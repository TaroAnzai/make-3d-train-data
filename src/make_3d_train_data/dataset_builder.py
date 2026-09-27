import hashlib
import json
import random
import re
import tempfile
from datetime import datetime
from pathlib import Path

import yaml
from PIL import Image, ImageEnhance, ImageFilter
from tqdm import tqdm

from .blender_runner import render_scene
from .class_defs import CLASSES
from .coco_writer import CocoWriter
from .manifest_writer import ManifestWriter
from .scene_generator import generate_scene
from .yolo_writer import write_yolo


def _postprocess(path, noise, seed):
    rng = random.Random(seed)
    im = Image.open(path).convert("RGB")
    im = ImageEnhance.Brightness(im).enhance(rng.uniform(*noise["brightness_range"]))
    im = ImageEnhance.Contrast(im).enhance(rng.uniform(*noise["contrast_range"]))
    if rng.random() < noise["blur_prob"]:
        im = im.filter(ImageFilter.GaussianBlur(rng.uniform(*noise["blur_sigma_range"])))
    im.save(path, "JPEG", quality=rng.randint(*map(int, noise["jpeg_quality_range"])))


def _pair(a: int, b: int) -> int:
    total = a + b
    return total * (total + 1) // 2 + b


def _natural(value: int) -> int:
    return value * 2 if value >= 0 else -value * 2 - 1


def _existing_datasets(output_root: Path, config_name: str):
    pattern = re.compile(rf"^{re.escape(config_name)}-(\d+)-(\d+)$")
    if not output_root.exists():
        return []
    return [(int(match.group(1)), path) for path in output_root.iterdir()
            if path.is_dir() and (match := pattern.fullmatch(path.name))]


def _reserve_dataset(output_root: Path, config_name: str, count: int):
    output_root.mkdir(parents=True, exist_ok=True)
    number = max((number for number, _ in _existing_datasets(output_root, config_name)), default=0) + 1
    while True:
        root = output_root / f"{config_name}-{number:02d}-{count}"
        try:
            root.mkdir()
            return root, number
        except FileExistsError:
            number += 1


def _image_hash(path: Path) -> bytes:
    digest = hashlib.sha256()
    with path.open("rb") as image:
        for chunk in iter(lambda: image.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.digest()


def build_dataset(config, blender_bin=None):
    output = config["output"]
    output_root = Path(output["root"]).expanduser()
    config_name = Path(config.get("_config_path", "dataset.yaml")).stem
    seen = {_image_hash(path) for path in output_root.glob("*/images/*.jpg")}
    root, number = _reserve_dataset(output_root, config_name, output["count"])
    images, annotations, meta = root / "images", root / "annotations", root / "meta"
    for path in (images, annotations, meta):
        path.mkdir()
    dataset_name = f"cg_{datetime.now().astimezone():%Y%m%d}_{number:03d}"
    (root / "dataset.yaml").write_text(yaml.safe_dump({"name": dataset_name, "format": "coco", "class_schema": "canonical37"}, sort_keys=False), encoding="utf-8")
    coco = CocoWriter()
    manifest = ManifestWriter(meta / "manifest.jsonl")
    (meta / "manifest.jsonl").write_text("", encoding="utf-8")

    # Pairing gives each config seed, dataset number, and render attempt a distinct seed.
    run_seed = _pair(_natural(int(config["general"]["seed"])), number)
    run_config = {**config, "general": {**config["general"], "seed": run_seed}}
    with tempfile.TemporaryDirectory(prefix="mahjong_render_") as tmp, tqdm(
        total=output["count"], desc="Generating", unit="image"
    ) as progress:
        for i in range(1, output["count"] + 1):
            name = f"{i:06d}.jpg"
            image_path = images / name
            for retry in range(10):
                attempt = (i - 1) + retry * output["count"]
                seed = _pair(run_seed, attempt)
                scene = generate_scene(run_config, i - 1, seed=seed)
                result = render_scene(scene, run_config, Path(tmp) / f"scene_{i}.json", Path(tmp) / f"result_{i}.json", image_path, blender_bin)
                _postprocess(image_path, scene.noise, scene.seed)
                digest = _image_hash(image_path)
                if digest not in seen:
                    seen.add(digest)
                    break
            else:
                image_path.unlink(missing_ok=True)
                raise ValueError(f"Could not generate a unique image after 10 attempts: {name}")

            anns = result["annotations"]
            coco.add_image(i, name, output["image_width"], output["image_height"], anns)
            if "yolo" in output["formats"]:
                write_yolo(annotations / "yolo" / f"{i:06d}.txt", anns, output["image_width"], output["image_height"])
            scene_data = scene.to_dict()
            manifest.append({"image": name, "seed": scene.seed, "width": output["image_width"], "height": output["image_height"], "mode": scene.mode, "tiles": anns, "camera": scene_data["camera"], "lighting": scene_data["lighting"], "background": scene.background, "appearance": scene.appearance, "occlusion": scene.occlusion})
            progress.update(1)

    coco.write(annotations / "instances.json")
    (meta / "classes.json").write_text(json.dumps([{"canonical_id": c.canonical_id, "name": c.name, "yolo_id": c.canonical_id - 1} for c in CLASSES], indent=2) + "\n", encoding="utf-8")
    clean = {k: v for k, v in config.items() if not k.startswith("_")}
    (meta / "used_config.yaml").write_text(yaml.safe_dump(clean, sort_keys=False), encoding="utf-8")
    (meta / "generation_summary.json").write_text(json.dumps({"images": output["count"], "dataset": dataset_name, "formats": sorted(set(output["formats"]) | {"coco"})}, indent=2) + "\n", encoding="utf-8")
    return root
