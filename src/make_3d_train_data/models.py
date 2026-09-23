from dataclasses import asdict, dataclass, field
from typing import Any

@dataclass
class TileInstance:
    class_id: int
    class_name: str
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    rotation_x: float = 0.0
    rotation_y: float = 0.0
    rotation_z: float = 0.0
    scale: float = 1.0
    face_down: bool = False
    annotate: bool = True

@dataclass
class CameraDescription:
    distance: float = 8.0
    tilt_deg: float = 60.0
    yaw_deg: float = 0.0
    roll_deg: float = 0.0
    target_x: float = 0.0
    target_y: float = 0.0
    target_z: float = 0.0
    lens_mm: float = 52.0
    dof_enabled: bool = False
    focus_distance: float = 10.0
    aperture_fstop: float = 5.6

@dataclass
class LightingDescription:
    intensity: float = 1.0

@dataclass
class SceneDescription:
    seed: int
    mode: str
    tiles: list[TileInstance]
    camera: CameraDescription = field(default_factory=CameraDescription)
    lighting: LightingDescription = field(default_factory=LightingDescription)
    background: dict[str, Any] = field(default_factory=dict)
    noise: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
