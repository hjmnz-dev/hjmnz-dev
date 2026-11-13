"""Prepare a portrait for ASCII conversion (run locally, once per photo).

1. Remove the background with rembg.
2. Boost local contrast with OpenCV CLAHE.
3. Composite onto pure white and crop to the subject.

Usage: python scripts/prep_photo.py path/to/photo.jpg
Writes: source-prepped.png (grayscale) and source-mask.png (subject alpha)
"""
import io
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "source-prepped.png"
MASK = ROOT / "source-mask.png"


def main(src: str) -> None:
    raw = Path(src).read_bytes()
    cut = Image.open(io.BytesIO(remove(raw))).convert("RGBA")
    rgba = np.array(cut)
    alpha = rgba[:, :, 3].astype(np.float32) / 255.0

    gray = cv2.cvtColor(rgba[:, :, :3], cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    gray = clahe.apply(gray).astype(np.float32)

    # Composite onto white so the background maps to the blank end of the ramp.
    out = gray * alpha + 255.0 * (1.0 - alpha)
    out = out.clip(0, 255).astype(np.uint8)

    # Crop to the subject, square-ish, with a little headroom.
    ys, xs = np.where(alpha > 0.1)
    top, bottom = max(ys.min() - 20, 0), out.shape[0]
    left, right = max(xs.min() - 10, 0), min(xs.max() + 10, out.shape[1])
    out = out[top:bottom, left:right]
    mask = (alpha[top:bottom, left:right] * 255).astype(np.uint8)

    Image.fromarray(out).save(OUT)
    Image.fromarray(mask).save(MASK)
    print(f"wrote {OUT.name} {out.shape[1]}x{out.shape[0]}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python scripts/prep_photo.py photo.jpg")
    main(sys.argv[1])
