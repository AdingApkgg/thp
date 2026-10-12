#!/usr/bin/env python3
"""Locate the counterpart, in one title's image, of a global variable in another title's.

The oracle fixtures in `tests/cpp` name one title's *data* addresses as well as its code: game-state
pointers, the animation manager's slot, the character and shot of a dialogue. A global has no
instructions of its own, so the way to find its counterpart is through the code that reads it: the
same engine function in the other title reads its own global from the same place in the same
instructions.

`th-twin-find.py` matches a code window with every byte of an in-image dword masked - and the masked
bytes of a window that references a global are exactly that global's address. So for each reference
site, the twin's bytes at those same offsets *are* the counterpart's address. Sites that agree give
the answer; sites that do not are printed so a reviewer can see the disagreement.

Usage: th-twin-global.py <from.exe> <0xGLOBAL> <to.exe> [--span 28] [--min-run 8] [--top 8]
       [--sites N] [--scan N] the caps below
       [--sites N]  follow at most N reference sites (a global can have hundreds)
"""
import collections
import importlib.util
import os
import struct
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location('twinfind', os.path.join(_HERE, 'th-twin-find.py'))
twinfind = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(twinfind)


def reference_sites(blob, base, ceiling, value):
    """Every position in .text whose immediate is `value`."""
    needle = struct.pack('<I', value)
    sites = []
    at = blob.find(needle)
    while at >= 0:
        sites.append(at)
        at = blob.find(needle, at + 1)
    return sites


def main():
    source, global_argument, target = sys.argv[1], sys.argv[2], sys.argv[3]
    span = int(sys.argv[sys.argv.index('--span') + 1], 0) if '--span' in sys.argv else 28
    min_run = int(sys.argv[sys.argv.index('--min-run') + 1], 0) if '--min-run' in sys.argv else 8
    top = int(sys.argv[sys.argv.index('--top') + 1], 0) if '--top' in sys.argv else 8
    value = int(global_argument, 0)

    from_va, from_blob, from_base, from_ceiling = twinfind.image_text(source)
    to_va, to_blob, to_base, to_ceiling = twinfind.image_text(target)
    # --sites counts decisive sites: most byte occurrences of a value are not instructions
    # (0x4c3268 shares bytes with other operands), so stop after enough of them decode
    sites_limit = int(sys.argv[sys.argv.index('--sites') + 1], 0) if '--sites' in sys.argv else None
    # a small constant's bytes occur thousands of times in a 600 KiB text; --scan caps how
    # many raw sites are tried before giving up on finding enough decisive ones
    scan = int(sys.argv[sys.argv.index('--scan') + 1], 0) if '--scan' in sys.argv else None
    sites = reference_sites(from_blob, from_base, from_ceiling, value)
    if scan:
        sites = sites[:scan]
    print('  %s 0x%x: %d reference(s)' % (source, value, len(sites)))
    if not sites:
        return

    candidates = collections.Counter()
    detail = []
    decisive = 0
    for where in sites:
        if sites_limit and decisive >= sites_limit:
            break
        start = max(0, where - 4)
        if start + span > len(from_blob):
            continue
        signature = twinfind.normalize(from_blob[start:start + span], from_base, from_ceiling, span)
        # where this window carries the value: the exact bytes, whether they are a data address
        # (masked by the in-image rule) or a plain immediate such as a structure's size
        packed = struct.pack('<I', value)
        first = -1
        for start_at in range(max(0, where - start) - 0, min(span, where - start + 4)):
            if bytes(from_blob[start + start_at:start + start_at + 4]) == packed:
                first = start_at
                break
        held = [first + k for k in range(4)] if first >= 0 and first + 4 <= span else []
        best = None
        for candidate in range(len(to_blob) - span):
            run, matches, literals = twinfind.score(signature, to_blob, candidate)
            if run >= min_run and (best is None or run > best[0]):
                best = (run, matches, candidate)
        if best is None:
            detail.append((from_va + where, None, 0, None))
            continue
        _, _, candidate = best
        window = to_blob[candidate:candidate + span]
        # the twin's bytes where the source held the address are the counterpart's address
        offsets = [index for index in held if (start + index) >= where
                   and (start + index) < where + 4]
        if len(offsets) == 4:
            found = struct.unpack_from('<I', bytes(window[index] for index in offsets), 0)[0]
            # a global decodes inside the target image; a plain constant such as a
            # structure's size is simply a small immediate
            possible = found if 0 < found < 0x10000000 else None
            if possible:
                candidates[possible] += 1
                decisive += 1
            detail.append((from_va + where, to_va + candidate, best[0],
                          possible))
        else:
            detail.append((from_va + where, to_va + candidate, best[0], None))
    print('  candidate counterpart(s) by agreement across reference sites:')
    for address, count in candidates.most_common(top):
        print('    0x%08x  %d/%d site(s)' % (address, count, len(sites)))
    print('  per-site detail (reference site -> twin, run, decoded value):')
    for site, twin, run, decoded in detail[:12]:
        print('    0x%08x -> %s run %s -> %s'
              % (site, ('0x%08x' % twin) if twin else 'none', run,
                 ('0x%08x' % decoded) if decoded else 'none'))
    # the same-title check: from == to must decode to the input
    if source == target:
        print('  self-check: candidates include the input address: %s'
              % ('yes' if value in candidates else 'NO'))


if __name__ == '__main__':
    main()
