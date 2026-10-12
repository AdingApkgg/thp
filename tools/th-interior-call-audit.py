"""Find every suite call into a function's interior whose epilogue will not balance.

A function's shared epilogue pops the registers its prologue pushed. A suite that enters at a label
inside the function - a jump-table case, say - skips that prologue, and the epilogue then pops the
caller's frame instead of its own saved registers. The `ret` that follows reads an argument as the return
address, which is a fetch at whatever the argument happens to be - zero, in the pc=0x0 cluster of rounds
313 to 315, where the last executed address was 0x44ae9d `ret` after `pop edi; pop esi; pop ebx`.

For every `m.call(<literal>)` in the suites this asks whether the literal is an entry in the image's
call-target index, and for the ones that are not it compares the function's epilogue with the region
from the label to the end of the function. Both earlier boundaries were wrong and are recorded here
because the same trap will catch the next reader: stopping at the first `ret` misses a shared epilogue
reached by a jump (`0x44acd0` reaches 0x44ae98 through `jnp`, and the first `ret` in the linear stream
comes earlier), and stopping at the next call target truncates the function at one of its own interior
labels. The end of the function is its padding - MSVC separates functions with `int3` runs or the
`mov edi, edi` hot-patch pair - which is a fact about the image rather than a guess about layout.

  py -3 tools/th-interior-call-audit.py --title th12
"""
import argparse
import io
import os
import re
import struct
import importlib.util

import capstone

_ARGS = argparse.ArgumentParser()
_ARGS.add_argument('--title', default='th12')
_ARGS.add_argument('--tests', default=None)
_ARGS.add_argument('--image', default=None)
_OPTS = _ARGS.parse_args()

IMAGE = _OPTS.image or 'H:/Games/th/12/th12.exe'
TESTS = _OPTS.tests or os.path.join('runtimes', 'th12', 'th12_web', 'tests', 'cpp')
MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
MD.detail = True

_spec = importlib.util.spec_from_file_location('tb', os.path.join('tools', 'th-twin-batch.py'))
batch = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(batch)


def text_of(image):
    data = io.open(image, 'rb').read()
    pe = struct.unpack_from('<I', data, 0x3c)[0]
    count = struct.unpack_from('<H', data, pe + 6)[0]
    header = struct.unpack_from('<H', data, pe + 20)[0]
    for index in range(count):
        offset = pe + 24 + header + index * 40
        name = data[offset:offset + 8].rstrip(b'\x00').decode('latin1')
        virtual_size, va, raw_size, raw = struct.unpack_from('<IIII', data, offset + 8)
        if name == '.text':
            return data[raw:raw + raw_size], 0x400000 + va
    return None, None


def block_end(blob, base, entry):
    """The offset one past the function that starts at entry, found by the padding that follows it."""
    start = entry - base
    for offset in range(start, min(start + 0x4000, len(blob) - 2)):
        byte = blob[offset]
        if byte == 0xcc and blob[offset + 1] == 0xcc:
            return offset
        if byte in (0xc3, 0xc2):
            after = blob[offset + 1]
            if after == 0xcc or (after == 0x8b and blob[offset + 2] == 0xff):
                return offset + 1
    return min(start + 0x4000, len(blob))


def main():
    blob, base = text_of(IMAGE)
    entries = sorted(batch.call_targets(MD, blob, base))
    entry_set = set(entries)
    pattern = re.compile(r'm\.call\(\s*(0x[0-9a-fA-F]+)')
    rows = []
    for name in sorted(os.listdir(TESTS)):
        if not name.endswith('.test.mjs'):
            continue
        text = io.open(os.path.join(TESTS, name), encoding='utf-8').read()
        for match in pattern.finditer(text):
            address = int(match.group(1), 16)
            line = text[:match.start()].count('\n') + 1
            if address in entry_set:
                continue
            entry = max((candidate for candidate in entries if candidate <= address), default=None)
            if entry is None:
                rows.append((name, line, address, None, 'no enclosing entry'))
                continue
            end = block_end(blob, base, entry)
            stream = list(MD.disasm(blob[entry - base:end], entry))
            inside = [insn for insn in stream if insn.address >= address]
            pops = [insn for insn in inside if insn.mnemonic in ('pop', 'popal', 'popad', 'popfd')]
            pushes = [insn for insn in inside if insn.mnemonic in ('push', 'pushal', 'pushad', 'pushfd')]
            leaves = [insn for insn in inside if insn.mnemonic == 'leave']
            balance = len(pops) - len(pushes) - len(leaves)
            rows.append((name, line, address, entry, balance))
    unbalanced = [row for row in rows if isinstance(row[4], int) and row[4] > 0]
    print('  %s: %d literal call sites into non-entry addresses, %d of them pop more than they push'
          % (IMAGE, len(rows), len(unbalanced)))
    for name, line, address, entry, balance in rows:
        if isinstance(balance, int):
            verdict = ('epilogue pops %d more than the entered region pushes - the ret reads a caller slot'
                       % balance) if balance > 0 else 'balanced from this label'
            print('    %-28s L%-4d 0x%08x (entry 0x%08x)  %s' % (name, line, address, entry, verdict))
        else:
            print('    %-28s L%-4d 0x%08x  %s' % (name, line, address, balance))


main()
