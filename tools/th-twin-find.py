#!/usr/bin/env python3
"""Locate the counterpart, in one title's image, of a code window in another title's.

The oracle fixture files (`tests/cpp/*.mjs`) name addresses of the title the port started from. Porting
them to another title means asking "which function here is the one that was at that address there",
and the answer is a *code* match, not a guess: an engine function keeps its instructions and its field
offsets between titles, while the addresses it calls and the globals it reads change.

The signature is the window's bytes with every four-byte little-endian value that points inside the
image replaced by zeros. That single rule covers both call displacements and absolute data references,
which is exactly the set of operands that must differ between two images; immediates and structure
(such as `push 0x434` or `[esi+0x3e8]`) stay literal and carry the match.

Usage:
  th-twin-find.py <from.exe> <0xADDR> <to.exe> [--span 48] [--top 5] [--expect 0xADDR]

The instrument checks itself before it is trusted with an answer:
  * an identical-title round trip must return the source address at score 1.0, and
  * `--expect` must be in the reported list.
"""
import struct
import sys


def image_text(path):
    image = open(path, 'rb').read()
    pe = struct.unpack_from('<I', image, 0x3C)[0]
    count = struct.unpack_from('<H', image, pe + 6)[0]
    option = struct.unpack_from('<H', image, pe + 20)[0]
    base = struct.unpack_from('<I', image, pe + 24 + 28)[0]
    for index in range(count):
        at = pe + 24 + option + index * 40
        name = image[at:at + 8].split(b'\x00')[0].decode('ascii', 'replace')
        vsize, rva, rawsize, raw = struct.unpack_from('<IIII', image, at + 8)
        if name == '.text':
            size = max(vsize, rawsize)
            # Every operand an engine function embeds points into the image: a call displacement into
            # .text and an absolute reference into .data, which sits at a higher address. The whole
            # image window is therefore the rule that decides what a title-to-title difference may
            # touch, and its ceiling is the load address of the highest section.
            ceiling = 0
            for other in range(count):
                oat = pe + 24 + option + other * 40
                ovsize, orva, orawsize, oraw = struct.unpack_from('<IIII', image, oat + 8)
                ceiling = max(ceiling, base + orva + max(ovsize, orawsize))
            return base + rva, image[raw:raw + size], base, ceiling
    raise SystemExit('no .text in %s' % path)


def normalize(blob, base, higher, span):
    """The window's bytes, with every byte of an in-image dword marked as an operand.

    A difference between two titles' copies of one engine function lands on the operands that name an
    address: a call or jump displacement into .text, or an absolute reference to a global in .data.
    Those bytes are exactly the ones covered by a four-byte in-image value, so the rule marks a byte
    when a dword overlapping it is in-image - which catches a displacement whose bytes are spread over
    the comparison window as well as one that is aligned inside it.
    """
    wild = [False] * span
    for offset in range(span):
        for start in range(max(0, offset - 3), min(offset + 1, span - 3)):
            word = struct.unpack_from('<I', blob, start)[0]
            if base <= word < higher:
                wild[offset] = True
    return [(0 if wild[offset] else blob[offset], wild[offset]) for offset in range(span)]


def score(signature, blob, at):
    """Rank a candidate by its longest run of agreeing literals, then by how many literals agree.

    A run is what makes a match meaningful: two titles' copies of one function share a long stretch
    of identical instruction bytes even when a call's displacement, an offset that moved, or a whole
    extra block differs somewhere in the window.
    """
    run = best_run = 0
    matches = literals = 0
    for index, (value, wild) in enumerate(signature):
        if wild:
            run = 0
            continue
        literals += 1
        if blob[at + index] == value:
            matches += 1
            run += 1
            if run > best_run:
                best_run = run
        else:
            run = 0
    return best_run, matches, literals


def main():
    source, at_argument, target = sys.argv[1], sys.argv[2], sys.argv[3]
    span = int(sys.argv[sys.argv.index('--span') + 1], 0) if '--span' in sys.argv else 48
    top = int(sys.argv[sys.argv.index('--top') + 1], 0) if '--top' in sys.argv else 5
    expect = int(sys.argv[sys.argv.index('--expect') + 1], 0) if '--expect' in sys.argv else None
    source_va = int(at_argument, 0)
    min_run = int(sys.argv[sys.argv.index('--min-run') + 1], 0) if '--min-run' in sys.argv else 12

    from_va, from_blob, from_base, from_higher = image_text(source)
    to_va, to_blob, to_base, to_higher = image_text(target)
    offset = source_va - from_va
    if offset < 0 or offset + span > len(from_blob):
        raise SystemExit('0x%x is not in the source .text' % source_va)
    signature = normalize(from_blob[offset:offset + span], from_base, from_higher, span)

    # identical-title round trip: the same address must come back at score 1.0
    if source == target:
        run = score(signature, to_blob, offset)[0]
        print('  self-check: 0x%x -> longest literal run %d (must be the whole window)'
              % (source_va, run))

    hits = []
    for candidate in range(len(to_blob) - span):
        run, matches, literals = score(signature, to_blob, candidate)
        if run >= min_run:
            hits.append((run, matches, literals, to_va + candidate,
                        to_blob[candidate:candidate + 12]))
    hits.sort(key=lambda row: (-row[0], -row[1], row[3]))
    print('  %s 0x%x -> %s: %d candidate(s) with a run of %d or more'
          % (source, source_va, target, len(hits), min_run))
    for run, matches, literals, address, head in hits[:top]:
        print('    run %d/%d literals %d  0x%08x  %s'
              % (run, len(signature), literals, address,
                 ' '.join('%02x' % b for b in head)))
    if expect is not None:
        found = [row[3] for row in hits]
        print('  expect: 0x%x %s' % (expect, 'listed' if expect in found else 'MISSING'))


if __name__ == '__main__':
    main()
