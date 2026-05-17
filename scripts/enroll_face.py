"""
Face enrollment script.

Usage:
  python enroll_face.py --name "Jarno" --webcam [--count 10]
  python enroll_face.py --name "Jarno" --images /path/to/photos/
  python enroll_face.py --list
  python enroll_face.py --remove "Jarno"
"""
from __future__ import annotations

import argparse
import logging
import pickle
from pathlib import Path

import cv2
import face_recognition
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("enroll")

EMBEDDINGS_DIR = Path("shared/embeddings")
EMBEDDINGS_FILE = EMBEDDINGS_DIR / "embeddings.pkl"


def _load() -> tuple[list, list]:
    if EMBEDDINGS_FILE.exists():
        with open(EMBEDDINGS_FILE, "rb") as f:
            data = pickle.load(f)
        return data.get("encodings", []), data.get("names", [])
    return [], []


def _save(encodings: list, names: list) -> None:
    EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(EMBEDDINGS_FILE, "wb") as f:
        pickle.dump({"encodings": encodings, "names": names}, f)
    logger.info("Saved %d embeddings → %s", len(names), EMBEDDINGS_FILE)


def _encode(path: Path) -> np.ndarray | None:
    img = face_recognition.load_image_file(str(path))
    locs = face_recognition.face_locations(img)
    if not locs:
        logger.warning("No face in %s – skipped", path.name)
        return None
    encs = face_recognition.face_encodings(img, locs[:1])
    return encs[0] if encs else None


def enroll_from_images(name: str, image_dir: str) -> int:
    encodings, names = _load()
    count = 0
    for p in sorted(Path(image_dir).iterdir()):
        if p.suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp"}:
            continue
        enc = _encode(p)
        if enc is not None:
            encodings.append(enc)
            names.append(name)
            count += 1
            logger.info("  ✓ %s", p.name)
    if count:
        _save(encodings, names)
    return count


def enroll_from_webcam(name: str, num_photos: int = 10) -> int:
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logger.error("Cannot open webcam")
        return 0
    encodings, names = _load()
    count = 0
    logger.info("Press SPACE to capture (%d needed), Q to quit", num_photos)

    while count < num_photos:
        ret, frame = cap.read()
        if not ret:
            continue
        overlay = frame.copy()
        status = f"Captured {count}/{num_photos}  |  SPACE = snap  Q = quit"
        cv2.putText(overlay, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (50, 255, 80), 2)

        # Draw face boxes live
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        locs = face_recognition.face_locations(rgb)
        for top, right, bottom, left in locs:
            cv2.rectangle(overlay, (left, top), (right, bottom), (50, 255, 80), 2)

        cv2.imshow("Face Enrollment – " + name, overlay)
        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break
        if key == ord(" "):
            if not locs:
                logger.warning("No face detected – try again")
                continue
            encs = face_recognition.face_encodings(rgb, locs[:1])
            if encs:
                encodings.append(encs[0])
                names.append(name)
                count += 1
                logger.info("  Snap %d/%d", count, num_photos)

    cap.release()
    cv2.destroyAllWindows()
    if count:
        _save(encodings, names)
    return count


def list_enrolled() -> None:
    _, names = _load()
    from collections import Counter
    counts = Counter(names)
    if not counts:
        print("No enrolled persons.")
        return
    print(f"Enrolled persons ({len(counts)}):")
    for person, n in sorted(counts.items()):
        print(f"  {person}: {n} samples")


def remove_person(name: str) -> None:
    encodings, names = _load()
    before = len(names)
    filtered = [(e, n) for e, n in zip(encodings, names) if n != name]
    if not filtered:
        encodings, names = [], []
    else:
        encodings, names = zip(*filtered)
        encodings, names = list(encodings), list(names)
    removed = before - len(names)
    _save(encodings, names)
    logger.info("Removed %d samples for '%s'", removed, name)


def main() -> None:
    parser = argparse.ArgumentParser(description="Enroll/manage face embeddings")
    parser.add_argument("--name", help="Person name")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--images", metavar="DIR", help="Directory with face images")
    group.add_argument("--webcam", action="store_true", help="Interactive webcam capture")
    group.add_argument("--list", action="store_true", help="List enrolled persons")
    group.add_argument("--remove", metavar="NAME", help="Remove person")
    parser.add_argument("--count", type=int, default=10, help="Webcam: photos to capture")
    args = parser.parse_args()

    if args.list:
        list_enrolled()
    elif args.remove:
        remove_person(args.remove)
    elif args.images:
        if not args.name:
            parser.error("--name required with --images")
        n = enroll_from_images(args.name, args.images)
        print(f"Enrolled {n} images for '{args.name}'")
    elif args.webcam:
        if not args.name:
            parser.error("--name required with --webcam")
        n = enroll_from_webcam(args.name, args.count)
        print(f"Enrolled {n} webcam captures for '{args.name}'")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
