from pathlib import Path
from shutil import copyfile

from .class_defs import CLASSES


_SOURCE_FILENAMES = {
    **{f"{number}m": f"Man{number}.png" for number in range(1, 10)},
    **{f"{number}p": f"Pin{number}.png" for number in range(1, 10)},
    **{f"{number}s": f"Sou{number}.png" for number in range(1, 10)},
    "east": "Ton.png",
    "south": "Nan.png",
    "west": "Shaa.png",
    "north": "Pei.png",
    "white": "Haku.png",
    "green": "Hatsu.png",
    "red": "Chun.png",
    "red5m": "Man5-Dora.png",
    "red5p": "Pin5-Dora.png",
    "red5s": "Sou5-Dora.png",
}


def _regular_texture_dir() -> Path:
    """Locate the bundled Regular artwork independently of the current cwd."""
    project_root = Path(__file__).resolve().parents[2]
    return project_root / "external" / "riichi-mahjong-tiles" / "Export" / "Regular"


def generate_textures(output_dir="assets/generated/textures"):
    """Copy the bundled Regular artwork to canonical dataset class filenames."""
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    source_root = _regular_texture_dir()

    generated = []
    for tile_class in CLASSES:
        source = source_root / _SOURCE_FILENAMES[tile_class.name]
        if not source.is_file():
            raise FileNotFoundError(f"Missing bundled tile texture: {source}")
        destination = output_root / f"{tile_class.name}.png"
        copyfile(source, destination)
        generated.append(destination)
    return generated
