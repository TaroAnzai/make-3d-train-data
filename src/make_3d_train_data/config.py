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
    "assets": {"tile_blend": "./assets/blender/tiles_master.blend", "mat_blend": "./assets/masters/table_assets.blend"},
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
    for name in ("tile_blend", "mat_blend"):
        if not isinstance(cfg["assets"].get(name), str) or not cfg["assets"][name]:
            raise ValueError(f"assets.{name} must be a file path")
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
    variations = cfg.get("variations", {})
    if variations.get("enabled"):
        if mode != "fixed":
            raise ValueError("variations requires scene.mode: fixed")
        for key in ("star3_probability", "star2_probability"):
            if not 0 <= variations[key] <= 1:
                raise ValueError(f"variations.{key} must be between 0 and 1")
        for path in (
            "variations.hand.x_offset_mm_range", "variations.hand.y_offset_mm_range",
            "variations.hand.rotation_z_deg_range", "variations.hand.spacing_mm_range",
            "variations.camera.distance_range", "variations.camera.tilt_deg_range",
            "variations.camera.yaw_deg_range", "variations.camera.roll_deg_range",
            "variations.camera.target_x_range", "variations.camera.target_y_range",
            "variations.lighting.intensity_range", "variations.noise.brightness_range",
            "variations.noise.contrast_range", "variations.noise.jpeg_quality_range",
            "variations.noise.blur_sigma_range", "variations.wall_shift_mm_range",
        ):
            _range(cfg, path)
        lighting = variations["lighting"]
        for name, bounds in (("key_position_ranges", ((-.6, -.1), (-.5, 0), (.5, 1.1))),
                             ("fill_position_ranges", ((.1, .6), (0, .5), (.35, .85)))):
            if name in lighting:
                axes = lighting[name]
                if not isinstance(axes, list) or len(axes) != 3:
                    raise ValueError(f"variations.lighting.{name} must contain X/Y/Z ranges")
                for axis, (minimum, maximum) in zip(axes, bounds):
                    _range({"axis": axis}, "axis", minimum=minimum, maximum=maximum)
        if "color_temperature_range" in lighting:
            _range(cfg, "variations.lighting.color_temperature_range", minimum=3500, maximum=7000)
        materials = variations.get("materials", {})
        if materials:
            for name, bounds in (("tile_roughness_range", (.25, .65)),
                                 ("tile_specular_range", (.2, .5)),
                                 ("felt_brightness_range", (.8, 1.2)),
                                 ("felt_roughness_range", (.75, 1)),
                                 ("felt_texture_strength_range", (0, .06))):
                _range(cfg, f"variations.materials.{name}", minimum=bounds[0], maximum=bounds[1])
            tint = materials.get("felt_tint_ranges")
            if not isinstance(tint, list) or len(tint) != 3:
                raise ValueError("variations.materials.felt_tint_ranges must contain RGB ranges")
            for axis in tint:
                _range({"axis": axis}, "axis", minimum=.5, maximum=1.2)
        if not 0 <= variations.get("hand_occlusion_probability", 0) <= .05:
            raise ValueError("variations.hand_occlusion_probability must be between 0 and 0.05")
        counts = variations["hand"]["count_options"]
        if counts != [13, 14]:
            raise ValueError("variations.hand.count_options must be [13, 14]")
        if not 0 <= variations["hand"]["face_up_probability"] <= 1:
            raise ValueError("variations.hand.face_up_probability must be between 0 and 1")
        if not isinstance(variations["camera"]["lens_mm"], (int, float)) or variations["camera"]["lens_mm"] <= 0:
            raise ValueError("variations.camera.lens_mm must be positive")
        groups = [item.get("group") for item in cfg["tiles_fixed"]]
        if groups.count("hand") != 13 or "discard" not in groups or "wall_back" not in groups:
            raise ValueError("variations requires 13 hand tiles and tagged discard/wall tiles")
        annotation_groups = variations["annotation_groups"]
        if not isinstance(annotation_groups, list) or not annotation_groups or not set(annotation_groups).issubset(set(groups)):
            raise ValueError("variations.annotation_groups must name tagged tile groups")
        for key in ("discard_max_removed", "wall_max_removed"):
            if not isinstance(variations[key], int) or variations[key] < 1:
                raise ValueError(f"variations.{key} must be a positive integer")
        if not 0 <= variations["noise"]["blur_conditional_probability"] <= 1:
            raise ValueError("variations.noise.blur_conditional_probability must be between 0 and 1")
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
