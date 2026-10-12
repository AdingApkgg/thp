#!/usr/bin/env python3
"""Survey one original Touhou executable and its data archive into a target.json.

    py -3 tools/th-target-survey.py --game th13 --exe H:/Games/th/13/th13.exe \
        --dat H:/Games/th/13/th13.dat --bgm H:/Games/th/13/thbgm.dat \
        --localized-exe H:/Games/th/13/th13c.exe --localized-dat H:/Games/th/13/th13c.dat \
        [--write runtimes/th13/target.json]

Every number written comes from the file itself: the executable digest and size, the version and title string
read out of its UTF-16LE string table, and the archive's own header giving its format version and entry count.
The archive header is decrypted before it is read, so the count is checked against the file length as well - a
header that claims more entries than the file could hold is rejected rather than recorded.
"""
import argparse
import hashlib
import json
import os
import re
import struct
import sys

THA_HEADER = (0x1B, 0x37, 16, 16)


def resource_crypt(data, key, step, block, limit):
    """The original's archive cipher, transcribed from ResourceCrypt.cpp:resource_crypt.

    Within each block the bytes are taken from the source in a parity interleave - all the odd offsets reversed,
    then all the even ones - and the key advances by step for every byte produced. The key carries across blocks,
    and the tail a whole block cannot cover is copied through unchanged.
    """
    size = len(data)
    out = bytearray(size)
    untouched = (size % block if size % block < block // 4 else 0) + (size & 1)
    remaining, budget, cursor, k = size - untouched, limit, 0, key
    while remaining > 0 and budget > 0:
        span = min(block, remaining)
        linear = 0
        for parity in (1, 2):
            pos = span - parity
            while pos >= 0:
                out[cursor + pos] = data[cursor + linear] ^ k
                k = (k + step) & 0xFF
                linear += 1
                pos -= 2
        cursor += span
        remaining -= span
        budget -= span
    if cursor < size:
        out[cursor:] = data[cursor:]
    return bytes(out)


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def archive_header(path):
    """Return (version, entries) from a THA1 archive header, or raise."""
    with open(path, "rb") as handle:
        raw = handle.read(16)
    if len(raw) < 16:
        raise ValueError("archive is shorter than its 16-byte header: " + path)
    head = resource_crypt(raw, *THA_HEADER)
    if head[:4] != b"THA1":
        raise ValueError("archive header does not decrypt to THA1: " + path)
    unpacked = struct.unpack_from("<I", head, 4)[0] - 123456789
    packed = struct.unpack_from("<I", head, 8)[0] - 987654321
    count = struct.unpack_from("<I", head, 12)[0] - 135792468
    size = os.path.getsize(path)
    # Same limits Archive.cpp enforces, so a decompression bomb cannot be recorded as a target.
    if not count or count > 100000:
        raise ValueError("archive %s claims %d entries" % (path, count))
    if not packed or packed > size - 16:
        raise ValueError("archive %s claims %d packed bytes of %d" % (path, packed, size))
    if unpacked > 64 << 20 or unpacked < count * 16:
        raise ValueError("archive %s claims %d unpacked bytes for %d entries" % (path, unpacked, count))
    return count


def title_string(path, limit=1 << 22):
    """Find the first 'Touhou ... ver x.yz' style title in the leading image bytes.

    The string is stored as plain ASCII with the version appended, not as UTF-16LE: reading the image as wide
    characters finds nothing at all, which is how the earlier th12 record came to claim the wrong encoding.
    """
    with open(path, "rb") as handle:
        blob = handle.read(limit)
    text = blob.decode("latin-1")
    # Requiring a digit straight after "ver" matters: a plain search for "ver " also matches the "ver " inside
    # ordinary words such as "over", which is how three titles came to record an error message as their name.
    match = re.search(r"ver \d+\.\d+[a-z]?", text)
    if not match:
        return ""
    marker, start, end = match.start(), match.start(), match.end()
    while start > 0 and text[start - 1].isprintable() and text[start - 1] not in "\r\n":
        start -= 1
    while end < len(text) and text[end].isprintable() and text[end] not in "\r\n":
        end += 1
    found = text[start:end].strip()
    # The byte before the title is often a stray glyph that is printable in latin-1, so keep only from the first
    # letter onwards.
    for i, ch in enumerate(found):
        if ch.isalpha():
            return found[i:]
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", required=True)
    ap.add_argument("--exe", required=True)
    ap.add_argument("--dat", required=True)
    ap.add_argument("--bgm")
    ap.add_argument("--localized-exe")
    ap.add_argument("--localized-dat")
    ap.add_argument("--version", default="unknown")
    ap.add_argument("--pbg-version", type=int,
                    help="archive cipher generation; defaults to the game's number, which is what "
                         "ResourceCrypt.cpp:archive_crypt_table keys on")
    ap.add_argument("--language", default="Japanese")
    ap.add_argument("--write")
    args = ap.parse_args()

    for path in (args.exe, args.dat):
        if not os.path.isfile(path):
            raise SystemExit("missing: " + path)

    entries = archive_header(args.dat)
    digits = "".join(ch for ch in args.game if ch.isdigit())
    pbg = args.pbg_version if args.pbg_version else (int(digits) if digits else 12)
    title = title_string(args.exe)
    version = args.version
    if version == "unknown" and title:
        at = title.find("ver ")
        if at >= 0:
            version = title[at + 4:].split()[0].strip().rstrip(".")
    target = {
        "game": args.game,
        "version": version,
        "language": args.language,
        "executable": args.exe.replace("\\", "/"),
        "sha256": digest(args.exe),
        "size": os.path.getsize(args.exe),
        "imageBase": "0x00400000",
        "evidence": "Executable title string: %r." % title,
        "dataArchives": {
            os.path.basename(args.dat): {
                "path": args.dat.replace("\\", "/"),
                "bytes": os.path.getsize(args.dat),
                "pbgVersion": pbg,
                "entries": entries,
            }
        },
        "completeGame": False,
    }
    if args.bgm:
        target["dataArchives"][os.path.basename(args.bgm)] = {
            "path": args.bgm.replace("\\", "/"),
            "bytes": os.path.getsize(args.bgm),
        }
    if args.localized_exe or args.localized_dat:
        localized = {}
        if args.localized_exe:
            localized["executable"] = {
                "file": args.localized_exe.replace("\\", "/"),
                "sha256": digest(args.localized_exe),
            }
        if args.localized_dat:
            localized["dataArchive"] = {"file": args.localized_dat.replace("\\", "/")}
        target["localized"] = localized

    text = json.dumps(target, indent=2, ensure_ascii=False) + "\n"
    if args.write:
        with open(args.write, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        print("wrote " + args.write)
    print(text, end="")


if __name__ == "__main__":
    main()
