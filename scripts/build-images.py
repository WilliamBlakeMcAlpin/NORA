#!/usr/bin/env python3
"""Derived images from NORA's own reference photos (refs/ is never edited).

macro-acetate-bw-*.jpg: black-and-white crops of refs/logo/nora-logo-amber.webp,
taken from areas clear of the logo. They stand in as sample macro shots until
real NORA photography exists. Amber is retired as a color, so these crops are
black and white only.
"""
import pathlib

from PIL import Image, ImageEnhance, ImageOps

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "refs/logo/nora-logo-amber.webp"
OUT = ROOT / "src/assets/images"

# (name, crop box in source px, output size). The logo sits around x 660-830, y 870-1170.
CROPS = [
    ("macro-acetate-bw-feed", (0, 1180, 656, 2000), (1080, 1350)),
    ("macro-acetate-bw-story", (840, 560, 1493, 1721), (1080, 1920)),
]


def bw(img):
    g = ImageOps.grayscale(img)
    g = ImageOps.autocontrast(g, cutoff=1)
    g = ImageEnhance.Contrast(g).enhance(1.35)
    # Pull the mids down: darkness dominates.
    g = g.point(lambda v: int(255 * (v / 255) ** 1.35))
    return g


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    src = Image.open(SRC).convert("RGB")
    for name, box, size in CROPS:
        im = bw(src.crop(box)).resize(size, Image.LANCZOS)
        im.save(OUT / f"{name}.jpg", quality=90)
        print(f"images: {name}.jpg {size[0]}x{size[1]}")


if __name__ == "__main__":
    main()
