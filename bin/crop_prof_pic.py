#!/usr/bin/env python3
"""Crop a portrait photo to a LinkedIn-style upper-body profile image."""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
from PIL import Image


def detect_face_center(image_bgr) -> tuple[int, int] | None:
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    detector = cv2.CascadeClassifier(cascade_path)
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    faces = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))
    if len(faces) == 0:
        return None
    x, y, w, h = max(faces, key=lambda box: box[2] * box[3])
    return x + w // 2, y + h // 2


def crop_upper_body(
    source: Path,
    destination: Path,
    *,
    bottom_ratio: float = 0.52,
    aspect_ratio: float = 0.82,
    output_size: int = 900,
) -> None:
    image = Image.open(source).convert("RGB")
    width, height = image.size

    face_center = None
    try:
        import numpy as np

        bgr = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        face_center = detect_face_center(bgr)
    except Exception:
        face_center = None

    center_x = face_center[0] if face_center else width // 2
    face_y = face_center[1] if face_center else int(height * 0.18)

    crop_bottom = min(height, int(height * bottom_ratio))
    crop_top = max(0, face_y - int((crop_bottom - face_y) * 0.35))

    crop_height = crop_bottom - crop_top
    crop_width = int(crop_height * aspect_ratio)
    left = max(0, min(center_x - crop_width // 2, width - crop_width))
    right = left + crop_width
    if right > width:
        right = width
        left = max(0, right - crop_width)

    cropped = image.crop((left, crop_top, right, crop_bottom))
    cropped = cropped.resize((output_size, int(output_size / aspect_ratio)), Image.Resampling.LANCZOS)
    destination.parent.mkdir(parents=True, exist_ok=True)
    cropped.save(destination, format="JPEG", quality=92, optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("assets/img/prof_pic_source.jpg"),
        help="Original portrait photo",
    )
    parser.add_argument(
        "--destination",
        type=Path,
        default=Path("assets/img/prof_pic.jpg"),
        help="Cropped profile image used by the site",
    )
    parser.add_argument(
        "--bottom-ratio",
        type=float,
        default=0.52,
        help="Crop bottom edge as a fraction of image height (chest/core)",
    )
    args = parser.parse_args()

    if not args.source.exists():
        raise SystemExit(f"Source image not found: {args.source}")

    crop_upper_body(args.source, args.destination, bottom_ratio=args.bottom_ratio)
    print(f"Wrote cropped profile image to {args.destination}")


if __name__ == "__main__":
    main()
