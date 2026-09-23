"""Build a labelled side-by-side image without changing the source photographs."""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def comparison(reference: Path, render: Path, output: Path,
               reference_box=None, render_box=None):
    size = 600
    margin = 24
    label_height = 52
    canvas = Image.new("RGB", (size * 2 + margin * 3, size + label_height + margin * 2), "#f2f2f0")
    font_path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    font = ImageFont.truetype(str(font_path), 22) if font_path.exists() else ImageFont.load_default()
    draw = ImageDraw.Draw(canvas)
    for index, (path, label, box) in enumerate(
        ((reference, "Real tile (low-resolution reference)", reference_box),
         (render, "Current master CG", render_box))
    ):
        with Image.open(path) as source:
            image = source.convert("RGB")
            if box is not None:
                image = image.crop(box)
            factor = min(size / image.width, size / image.height)
            image = image.resize((round(image.width * factor), round(image.height * factor)),
                                 Image.Resampling.BICUBIC)
        x = margin + index * (size + margin)
        canvas.paste(image, (x + (size - image.width) // 2,
                             margin + label_height + (size - image.height) // 2))
        draw.text((x, margin + 8), label, font=font, fill="#222222")
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--render", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reference-box", type=int, nargs=4)
    parser.add_argument("--render-box", type=int, nargs=4)
    args = parser.parse_args()
    comparison(args.reference, args.render, args.output,
               args.reference_box, args.render_box)


if __name__ == "__main__":
    main()
