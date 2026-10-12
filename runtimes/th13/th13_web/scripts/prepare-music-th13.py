"""Convert TH13's PCM to OGG, preserving every original loop/frame count.

TH13's thbgm.fmt has the same 52-byte record layout as TH11's and TH12's, and it was
measured before this script relied on it: record fields are
    <16s name> <u32 offset> <u32 preload> <u32 intro> <u32 length>
followed by a constant tail. Every record's offset + length lands exactly on the next
record's offset, so the layout is the file's whole content and not a guess.

The tail is the first thing TH13 does differently from TH12: the runtime serves 18 tracks
that are all 44100 Hz, while TH13 ships **two** rates. Its 31 records use
(1, 2, 44100, 176400, 4, 16) or (1, 2, 22050, 88200, 4, 16) - channels 2, 16 bits and a
4-byte align in both, and a byte rate of exactly rate * 4. AudioDevice::music reads the
rate at +36, the channels at +34 and the align at +44, so the encoder has to read the
same fields per record instead of one rate for the whole file.

The runtime asserts that a decoded track has exactly length/align PCM frames, so the encode
is verified by decoding it back and comparing shapes, not by trusting the encoder.

    python scripts/prepare-music-th13.py
"""
from pathlib import Path
import hashlib
import json
import struct
import sys

import numpy as np
import soundfile as sf

root = Path(__file__).resolve().parents[2]          # runtimes/th13
web = root / "th13_web"
out = web / "assets" / "sdl-native"
formats_path = web / "artifacts" / "cpp" / "th13-data" / "thbgm.fmt"
source_path = Path("H:/Games/th/13/thbgm.dat")
expected_tracks = 31
rates_seen = {22050: 0, 44100: 0}

if not formats_path.exists():
    sys.exit(f"missing {formats_path}\n"
             f"extract it first: thdat.exe -x d H:/Games/th/13/th13.dat thbgm.fmt")
if not source_path.exists():
    sys.exit(f"missing {source_path}")

(out / "music").mkdir(parents=True, exist_ok=True)
formats = formats_path.read_bytes()
report = []

with source_path.open("rb") as source:
    header = source.read(4)
    if header != b"ZWAV":
        sys.exit(f"{source_path} does not start with ZWAV (got {header!r})")

    record = 0
    at = 0
    while at + 52 <= len(formats) and formats[at]:
        name, offset, preload, intro, length = struct.unpack_from("<16sIIII", formats, at)
        name = name.split(b"\0")[0].decode("ascii")
        # +32 is the constant 1, then channels (u16), rate (u32), byte rate (u32),
        # align (u16) and bits (u16) - the same fields AudioDevice::music reads at
        # +34, +36, +44, which is why the widths here matter.
        channels, rate, byterate, align, bits = struct.unpack_from("<HIIHH", formats, at + 34)
        assert channels == 2 and bits == 16, f"{name}: {channels}ch {bits}bit"
        assert align == 4 and byterate == rate * align, f"{name}: odd align/byte rate"
        assert rate in rates_seen, f"{name}: unexpected rate {rate}"
        rates_seen[rate] += 1
        assert length % align == 0 and 0 <= intro < length and intro % align == 0, \
            f"{name}: bad loop"

        source.seek(offset)
        pcm = source.read(length)
        assert len(pcm) == length, f"{name}: short read"

        samples = np.frombuffer(pcm, dtype="<i2").reshape(-1, channels)
        path = out / "music" / (Path(name).stem + ".ogg")

        if not path.exists() or sf.info(str(path)).frames != len(samples):
            pending = path.with_suffix(".ogg.tmp")
            with sf.SoundFile(str(pending), "w", samplerate=rate, channels=channels,
                              subtype="VORBIS", format="OGG", compression_level=.4) as target:
                for start in range(0, len(samples), 16384):
                    target.write(samples[start:start + 16384].astype(np.float32) / 32768.)
            pending.replace(path)

        decoded, decoded_rate = sf.read(str(path), dtype="int16", always_2d=True)
        assert decoded.shape == samples.shape, \
            f"{name}: decoded {decoded.shape} != original {samples.shape}"
        assert decoded_rate == rate, f"{name}: rate {decoded_rate} != {rate}"

        report.append(dict(
            name=name, file=path.name, frames=len(samples), loopFrame=intro // align,
            rate=rate, channels=channels, encodedBytes=path.stat().st_size,
            pcmSha256=hashlib.sha256(pcm).hexdigest(),
            encodedSha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            codec="vorbis", lossless=False))
        print(f"{len(report)}/{expected_tracks} {name}: {len(samples)} PCM frames at "
              f"{rate} Hz, loop at {intro // align}", flush=True)
        record += 1
        at += 52

assert record == expected_tracks, f"expected {expected_tracks} tracks, got {record}"
(out / "music-verification.json").write_text(
    json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"tracks": len(report),
                  "rates": rates_seen,
                  "totalFrames": sum(t["frames"] for t in report),
                  "encodedBytes": sum(t["encodedBytes"] for t in report)}))
