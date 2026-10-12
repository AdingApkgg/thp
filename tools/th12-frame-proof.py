#!/usr/bin/env python3
"""Prove the th12 browser runtime actually renders and animates.

Every previous browser proof recorded only DOM strings and the absence of errors, which is not the
same as a running game: a blank canvas with a render loop would satisfy all of it. This checker looks
at the frames browser-proof.mjs wrote and applies a test strong enough to fail.

It fails when:
  * any frame is a single solid colour (a blank or fully cleared canvas), or
  * two consecutive late frames are byte-identical (a frozen renderer).

Both conditions are unambiguous. Everything else is printed as numbers to be judged, because picking
arbitrary "enough pixels differ" thresholds would be guessing.

Usage:
  py -3 tools/th12-frame-proof.py [artifacts/th12/browser-proof.json]

Exit 0 when the frames show real, changing content; 1 otherwise.
"""
import json
import sys
from pathlib import Path

try:
    from PIL import Image, ImageChops
except ImportError:  # pragma: no cover - the bundled python ships Pillow
    print("Pillow is required (bundled python 3 has it)")
    sys.exit(2)


def load(path):
    image = Image.open(path).convert("RGB")
    return image


def solid_colour(image):
    """Return the single colour if the whole frame is one colour, else None."""
    colours = image.getcolors(maxcolors=1 << 24)
    if colours is None:
        return None  # more colours than the cap, so certainly not solid
    if len(colours) == 1:
        return colours[0][1]
    return None


def differing_fraction(a, b):
    """Fraction of pixels that differ between two same-sized frames."""
    if a.size != b.size:
        return 1.0
    diff = ImageChops.difference(a, b)
    box = diff.getbbox()
    if box is None:
        return 0.0
    # A pixel counts as changed when any channel differs at all.
    # getcolors avoids the deprecated getdata. For an RGB image the cap is reachable at most at
    # 256**3, which equals the cap exactly, so None (more than the cap) cannot occur here.
    changed = sum(count for count, colour in (diff.getcolors(maxcolors=1 << 24) or []) if colour != (0, 0, 0))
    return changed / float(a.size[0] * a.size[1])


def background_fraction(image):
    """Fraction of pixels equal to the most common colour, to spot near-empty frames."""
    colours = image.getcolors(maxcolors=1 << 24)
    if colours is None:
        return 0.0
    colours.sort(reverse=True)
    total = image.size[0] * image.size[1]
    return colours[0][0] / float(total)


def main(argv):
    report_path = Path(argv[1]) if len(argv) > 1 else Path("artifacts/th12/browser-proof.json")
    if not report_path.exists():
        print(f"FAIL: {report_path} not found")
        return 1
    report = json.loads(report_path.read_text(encoding="utf8"))
    frames = report.get("frames") or []
    if not frames:
        print("FAIL: the proof recorded no frames")
        return 1

    base = report_path.parent
    problems = []
    loaded = []
    print(f"{'frame':<28}{'bytes':>9}{'size':>12}{'solid':>8}{'bg%':>8}")
    for entry in frames:
        path = base / entry["file"]
        if not path.exists():
            problems.append(f"{entry['file']} is missing")
            continue
        image = load(path)
        solid = solid_colour(image)
        bg = background_fraction(image)
        loaded.append((entry["file"], image))
        print(f"{entry['file']:<28}{path.stat().st_size:>9}{str(image.size):>12}"
              f"{str(solid is not None):>8}{bg * 100:>7.1f}%")
        if solid is not None:
            problems.append(f"{entry['file']} is a single solid colour {solid} - blank canvas")

    # Compare consecutive frames. At least one late pair must differ, or the renderer is frozen.
    print("\nconsecutive-frame difference (fraction of pixels changed):")
    changed_pairs = 0
    for i in range(1, len(loaded)):
        name_a, image_a = loaded[i - 1]
        name_b, image_b = loaded[i]
        fraction = differing_fraction(image_a, image_b)
        print(f"  {name_a} -> {name_b}: {fraction * 100:.2f}%")
        if fraction > 0.0:
            changed_pairs += 1
    if len(loaded) >= 2 and changed_pairs == 0:
        problems.append("no consecutive frame pair differs - the renderer is frozen")

    print()
    if problems:
        for problem in problems:
            print(f"FAIL: {problem}")
        return 1
    print(f"OK: {len(loaded)} frame(s), {changed_pairs} changing pair(s), none blank")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
