from dataclasses import dataclass

@dataclass(frozen=True)
class TileClass:
    canonical_id: int
    name: str

_NAMES = (
    [f"{n}m" for n in range(1, 10)]
    + [f"{n}p" for n in range(1, 10)]
    + [f"{n}s" for n in range(1, 10)]
    + ["east", "south", "west", "north", "white", "green", "red", "red5m", "red5p", "red5s"]
)
CLASSES = tuple(TileClass(i, name) for i, name in enumerate(_NAMES, 1))
BY_ID = {c.canonical_id: c for c in CLASSES}
BY_NAME = {c.name: c for c in CLASSES}

def resolve_class(value: str | int) -> TileClass:
    try:
        return BY_ID[int(value)] if isinstance(value, int) or str(value).isdigit() else BY_NAME[str(value)]
    except (KeyError, ValueError) as exc:
        raise ValueError(f"Unknown tile class: {value!r}") from exc

def coco_categories() -> list[dict]:
    return [{"id": c.canonical_id, "name": c.name, "supercategory": "mahjong_tile"} for c in CLASSES]

