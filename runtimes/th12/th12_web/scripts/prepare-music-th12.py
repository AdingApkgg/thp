"""Convert TH12's PCM to OGG, preserving every original loop/frame count.

TH12's thbgm.fmt has the same 52-byte record layout as TH11's, and this was
checked rather than assumed: record fields are
    <16s name> <u32 offset> <u32 preload> <u32 intro> <u32 length>
followed by the constant tail (1, 2, 44100, 176400, 4, 16) at +32, and each
record's offset + length lands exactly on the next record's offset.

The runtime asserts that a decoded track has exactly length/4 PCM frames, so
the encode is verified by decoding it back and comparing shapes, not by
trusting the encoder.

    python scripts/prepare-music-th12.py
"""
from pathlib import Path
import hashlib
import json
import struct
import sys

import numpy as np
import soundfile as sf

root = Path(__file__).resolve().parents[2]          # runtimes/th12
web = root / "th12_web"
out = web / "assets" / "sdl-native"
formats_path = web / "artifacts" / "cpp" / "th12-data" / "thbgm.fmt"
source_path = Path("H:/Games/th/12/thbgm.dat")

if not formats_path.exists():
    sys.exit(f"missing {formats_path}\n"
             f"extract it first: thdat.exe -x d H:/Games/th/12/th12.dat thbgm.fmt")
if not source_path.exists():
    sys.exit(f"missing {source_path}")

(out / "music").mkdir(parents=True, exist_ok=True)
formats = formats_path.read_bytes()
report = []

with source_path.open("rb") as source:
    header = source.read(4)
    if header != b"ZWAV":
        sys.exit(f"{source_path} does not start with ZWAV (got {header!r})")

    for at in range(0, len(formats) - 51, 52):
        if not formats[at]:
            break
        name, offset, preload, intro, length = struct.unpack_from("<16sIIII", formats, at)
        name = name.split(b"\0")[0].decode("ascii")
        tail = struct.unpack_from("<HHIIHH", formats, at + 32)
        assert tail == (1, 2, 44100, 176400, 4, 16), f"{name}: unexpected tail {tail}"
        assert length % 4 == 0 and 0 <= intro < length and intro % 4 == 0, f"{name}: bad loop"

        source.seek(offset)
        pcm = source.read(length)
        assert len(pcm) == length, f"{name}: short read"

        samples = np.frombuffer(pcm, dtype="<i2").reshape(-1, 2)
        path = out / "music" / (Path(name).stem + ".ogg")

        if not path.exists() or sf.info(str(path)).frames != len(samples):
            pending = path.with_suffix(".ogg.tmp")
            with sf.SoundFile(str(pending), "w", samplerate=44100, channels=2,
                              subtype="VORBIS", format="OGG", compression_level=.4) as target:
                for start in range(0, len(samples), 16384):
                    target.write(samples[start:start + 16384].astype(np.float32) / 32768.)
            pending.replace(path)

        decoded, rate = sf.read(str(path), dtype="int16", always_2d=True)
        assert decoded.shape == samples.shape, \
            f"{name}: decoded {decoded.shape} != original {samples.shape}"
        assert rate == 44100, f"{name}: rate {rate}"

        report.append(dict(
            name=name, file=path.name, frames=len(samples), loopFrame=intro // 4,
            encodedBytes=path.stat().st_size,
            pcmSha256=hashlib.sha256(pcm).hexdigest(),
            encodedSha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            codec="vorbis", lossless=False))
        print(f"{len(report)}/18 {name}: {len(samples)} PCM frames, "
              f"loop at {intro // 4}", flush=True)

assert len(report) == 18, f"expected 18 tracks, got {len(report)}"
(out / "music-verification.json").write_text(
    json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"tracks": len(report),
                  "totalFrames": sum(t["frames"] for t in report),
                  "encodedBytes": sum(t["encodedBytes"] for t in report)}))
