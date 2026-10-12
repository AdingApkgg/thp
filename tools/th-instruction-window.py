"""Print the instruction window around an address, from an entry that makes it an instruction boundary.

The entry index contains padding entries, so the enclosing entry is not necessarily a function start -
0x46022b decodes as `mov dh, bh`. This walks the candidate entries below the address and keeps the sweep
in which the address is exactly an instruction boundary, which is a check on the disassembly rather than
an assumption about it.
"""
import importlib.util
import io
import os
import struct
import sys

import capstone

spec = importlib.util.spec_from_file_location('tb', 'tools/th-twin-batch.py')
batch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(batch)
MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
MD.detail = True


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


def main():
    image = sys.argv[1]
    at = int(sys.argv[2], 16)
    after = int(sys.argv[3], 0) if len(sys.argv) > 3 else 12
    blob, base = text_of(image)
    entries = sorted(batch.call_targets(MD, blob, base))
    for entry in reversed([e for e in entries if e <= at][-40:]):
        stream = list(MD.disasm(blob[entry - base:entry - base + 0x600], entry))
        index = next((i for i, insn in enumerate(stream) if insn.address == at), None)
        if index is None:
            continue
        print('  %s: 0x%x is a boundary in the sweep from entry 0x%x' % (image, at, entry))
        for insn in stream[index:index + after]:
            print('    0x%08x  %-9s %s' % (insn.address, insn.mnemonic, insn.op_str))
        return
    print('  no entry makes 0x%x an instruction boundary' % at)


main()
