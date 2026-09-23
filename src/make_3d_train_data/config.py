from __future__ import annotations
from copy import deepcopy
from pathlib import Path
from typing import Any
import yaml
from .class_defs import resolve_class

DEFAULTS: dict[str, Any] = {
    "general": {"seed": 12345},
    "output": {"root": "./output", "dataset_name": "dataset", "image_width": 1280, "image_height": 720, "count": 1, "formats": ["coco"]},
    "blender": {"binary": None, "samples": 32, "engine": "BLENDER_EEVEE"},
    "scene": {"mode": "random", "background": {"enabled": False, "path": "./assets/backgrounds"}, "camera": {"distance_range": [6, 10], "tilt_deg_range": [40, 80], "yaw_deg_range": [-25, 25], "roll_deg_range": [-5, 5]}, "lighting": {"intensity_range": [0.7, 1.5]}},
    "tiles": {"count_range": [8, 18], "allowed_classes": "all", "x_range": [-3.5, 3.5], "y_range": [-2, 2], "z_range": [0, 0.25], "scale_range": [0.8, 1.2], "rotation_x_range": [-8, 8], "rotation_y_range": [-8, 8], "rotation_z_range": [-30, 30], "overlap_ratio_range": [0, .25], "edge_crop_probability": .1, "small_tile_probability": .2, "small_scale_range": [.35, .65], "occlusion_enabled": True},
    "noise": {"blur_prob": .2, "blur_sigma_range": [.2, 1.2], "brightness_range": [.8, 1.2], "contrast_range": [.8, 1.2], "jpeg_quality_range": [70, 95]},
}

def _merge(base: dict, override: dict) -> dict:
    result = deepcopy(base)
    for key, value in override.items():
        result[key] = _merge(result[key], value) if isinstance(value, dict) and isinstance(result.get(key), dict) else value
    return result

def _range(cfg: dict, path: str, *, minimum=None, maximum=None) -> None:
    cur: Any = cfg
    for p in path.split("."):
        cur = cur[p]
    if not isinstance(cur, list) or len(cur) != 2 or not all(isinstance(x, (int, float)) for x in cur) or cur[0] > cur[1]:
        raise ValueError(f"{path} must be an ascending two-number range")
    if minimum is not None and cur[0] < minimum or maximum is not None and cur[1] > maximum:
        raise ValueError(f"{path} values are out of range")

def validate_config(cfg: dict) -> dict:
    mode = cfg["scene"]["mode"]
    if mode not in ("fixed", "random"):
        raise ValueError("scene.mode must be fixed or random")
    out = cfg["output"]
    for key in ("image_width", "image_height", "count"):
        if not isinstance(out[key], int) or out[key] <= 0:
            raise ValueError(f"output.{key} must be a positive integer")
    if not set(out["formats"]).issubset({"coco", "yolo"}):
        raise ValueError("output.formats may contain only coco and yolo")
    for path in ("tiles.count_range", "tiles.scale_range", "tiles.x_range", "tiles.y_range", "tiles.z_range", "scene.camera.distance_range", "scene.camera.tilt_deg_range", "scene.camera.yaw_deg_range", "scene.camera.roll_deg_range", "scene.lighting.intensity_range", "noise.brightness_range", "noise.contrast_range", "noise.jpeg_quality_range"):
        _range(cfg, path)
    for key in ("edge_crop_probability", "small_tile_probability"):
        if not 0 <= cfg["tiles"][key] <= 1:
            raise ValueError(f"tiles.{key} must be between 0 and 1")
    allowed = cfg["tiles"]["allowed_classes"]
    if allowed != "all":
        if not isinstance(allowed, list) or not allowed:
            raise ValueError("tiles.allowed_classes must be all or a non-empty list")
        for value in allowed: resolve_class(value)
    if mode == "fixed":
        if not cfg.get("tiles_fixed"):
            raise ValueError("fixed mode requires tiles_fixed")
        for item in cfg["tiles_fixed"]: resolve_class(item.get("class"))
    return cfg

def load_config(path: str | Path) -> dict:
    source = Path(path)
    try:
        raw = yaml.safe_load(source.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise ValueError(f"Cannot load config {source}: {exc}") from exc
    if not isinstance(raw, dict): raise ValueError("config root must be a mapping")
    cfg = _merge(DEFAULTS, raw)
    cfg["_config_path"] = str(source.resolve())
    return validate_config(cfg)
