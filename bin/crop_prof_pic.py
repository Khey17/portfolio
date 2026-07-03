#!/usr/bin/env python3
"""Crop a portrait photo to a LinkedIn-style upper-body profile image."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


def detect_face_box(image_rgb) -> tuple[int, int, int, int] | None:
    try:
        import cv2
        import numpy as np

        if not hasattr(cv2, "CascadeClassifier"):
            return None

        bgr = cv2.cvtColor(np.array(image_rgb), cv2.COLOR_RGB2BGR)
        detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        faces = detector.detectMultiScale(
            cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY),
            scaleFactor=1.08,
            minNeighbors=5,
            minSize=(80, 80),
        )
        if len(faces) == 0:
            return None
        x, y, w, h = max(faces, key=lambda box: box[2] * box[3])
        return int(x), int(y), int(w), int(h)
    except Exception:
        return None


def estimate_face_box(width: int, height: int) -> tuple[int, int, int, int]:
    """Fallback for full-body portraits with the subject centered slightly right."""
    face_h = int(height * 0.11)
    face_w = int(face_h * 0.85)
    cx = int(width * 0.56)
    cy = int(height * 0.36)
    return cx - face_w // 2, cy - face_h // 2, face_w, face_h


def crop_face_and_chest(
    source: Path,
    destination: Path,
    *,
    top_margin: float = 0.55,
    bottom_margin: float = 2.1,
    aspect_ratio: float = 0.82,
    output_size: int = 900,
) -> None:
    image = Image.open(source).convert("RGB")
    width, height = image.size

    face = detect_face_box(image) or estimate_face_box(width, height)
    x, y, fw, fh = face
    cx = x + fw // 2
    cy = y + fh // 2

    crop_top = max(0, y - int(fh * top_margin))
    crop_bottom = min(height, cy + int(fh * bottom_margin))
    crop_height = crop_bottom - crop_top
    crop_width = int(crop_height * aspect_ratio)

    left = max(0, min(cx - crop_width // 2, width - crop_width))
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
        default=Path("assets/img/profile_pic_source.png"),
        help="Original portrait photo",
    )
    parser.add_argument(
        "--destination",
        type=Path,
        default=Path("assets/img/prof_pic.jpg"),
        help="Cropped profile image used by the site",
    )
    parser.add_argument(
        "--top-margin",
        type=float,
        default=0.55,
        help="Space above the face as a multiple of face height",
    )
    parser.add_argument(
        "--bottom-margin",
        type=float,
        default=2.1,
        help="Distance below face center to crop bottom, as a multiple of face height",
    )
    args = parser.parse_args()

    if not args.source.exists():
        raise SystemExit(f"Source image not found: {args.source}")

    crop_face_and_chest(
        args.source,
        args.destination,
        top_margin=args.top_margin,
        bottom_margin=args.bottom_margin,
    )
    print(f"Wrote cropped profile image to {args.destination}")


if __name__ == "__main__":
    main()
