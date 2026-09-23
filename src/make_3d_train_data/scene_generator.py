import random
from pathlib import Path
from .class_defs import CLASSES, resolve_class
from .models import CameraDescription, LightingDescription, SceneDescription, TileInstance

def _uniform(rng: random.Random, values): return rng.uniform(float(values[0]), float(values[1]))

def generate_scene(config: dict, index: int = 0) -> SceneDescription:
    seed = int(config["general"]["seed"]) + index
    rng = random.Random(seed)
    scene_cfg, tiles_cfg = config["scene"], config["tiles"]
    camera_cfg = scene_cfg["camera"]
    camera = CameraDescription(
        distance=_uniform(rng, camera_cfg["distance_range"]),
        tilt_deg=_uniform(rng, camera_cfg["tilt_deg_range"]),
        yaw_deg=_uniform(rng, camera_cfg["yaw_deg_range"]),
        roll_deg=_uniform(rng, camera_cfg["roll_deg_range"]),
        target_x=float(camera_cfg.get("target_x", 0.0)),
        target_y=float(camera_cfg.get("target_y", 0.0)),
        target_z=float(camera_cfg.get("target_z", 0.0)),
        lens_mm=float(camera_cfg.get("lens_mm", 52.0)),
        dof_enabled=bool(camera_cfg.get("dof_enabled", False)),
        focus_distance=float(camera_cfg.get("focus_distance", 10.0)),
        aperture_fstop=float(camera_cfg.get("aperture_fstop", 5.6)),
    )
    lighting = LightingDescription(_uniform(rng, scene_cfg["lighting"]["intensity_range"]))
    tiles = _fixed_tiles(config) if scene_cfg["mode"] == "fixed" else _random_tiles(rng, tiles_cfg)
    background = dict(scene_cfg.get("background", {}))
    background.setdefault("color", [round(rng.uniform(.025, .22), 4) for _ in range(3)])
    if background.get("enabled"):
        candidates = sorted(p for p in Path(background.get("path", "")).glob("*") if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
        background["selected"] = str(rng.choice(candidates).resolve()) if candidates else None
    return SceneDescription(seed, scene_cfg["mode"], tiles, camera, lighting, background, dict(config.get("noise", {})))

def generate_scenes(config: dict, count: int | None = None):
    return [generate_scene(config, i) for i in range(count if count is not None else config["output"]["count"])]

def _fixed_tiles(config):
    result = []
    for data in config["tiles_fixed"]:
        cls = resolve_class(data["class"])
        result.append(TileInstance(cls.canonical_id, cls.name, **{k: data[k] for k in ("x", "y", "z", "rotation_x", "rotation_y", "rotation_z", "scale", "face_down") if k in data}))
    return result

def _random_tiles(rng, cfg):
    allowed = list(CLASSES) if cfg["allowed_classes"] == "all" else [resolve_class(v) for v in cfg["allowed_classes"]]
    lo, hi = map(int, cfg["count_range"])
    count = rng.randint(lo, hi)
    result = []
    for i in range(count):
        cls = rng.choice(allowed)
        scale = _uniform(rng, cfg["scale_range"])
        if rng.random() < cfg["small_tile_probability"]: scale *= _uniform(rng, cfg["small_scale_range"])
        x, y = _uniform(rng, cfg["x_range"]), _uniform(rng, cfg["y_range"])
        # Cluster selected tiles around an earlier tile. The configured upper overlap ratio controls frequency.
        overlap = _uniform(rng, cfg["overlap_ratio_range"])
        if result and rng.random() < overlap:
            anchor = rng.choice(result); x = anchor.x + rng.uniform(-.45, .45); y = anchor.y + rng.uniform(-.6, .6)
        if rng.random() < cfg["edge_crop_probability"]:
            x = rng.choice((-1, 1)) * rng.uniform(max(abs(cfg["x_range"][0]), abs(cfg["x_range"][1])) * .9, max(abs(cfg["x_range"][0]), abs(cfg["x_range"][1])) * 1.25)
        result.append(TileInstance(cls.canonical_id, cls.name, x, y, _uniform(rng, cfg["z_range"]), _uniform(rng, cfg["rotation_x_range"]), _uniform(rng, cfg["rotation_y_range"]), _uniform(rng, cfg["rotation_z_range"]), scale))
    return result
