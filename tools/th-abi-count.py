"""Count the arguments the original pushes before calling the fixture's texture-dimensions slot.

machine.ret(value, args) does ESP += 4 + args*4, so the registered argc is how many bytes the callee
pops. The caller's pushes are the other half of the contract, and they are visible in the instruction
stream - but only from an instruction boundary, because the middle of an instruction decodes as anything.
The sweep starts at the enclosing function entry, taken from the same entry index the batch tool derives
interiors from.
"""
import importlib.util
import io
import os
import struct
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


batch = load('twinbatch', os.path.join(os.path.dirname(_HERE), 'th-twin-batch.py'))
import capstone

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
    image = sys.argv[1] if len(sys.argv) > 1 else 'H:/Games/th/12/th12.exe'
    around = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x46025B
    depth = int(sys.argv[3], 0) if len(sys.argv) > 3 else 12
    blob, base = text_of(image)
    entries = sorted(batch.call_targets(MD, blob, base))
    candidates = [e for e in entries if e <= around][-depth:]
    print('  %s, return address 0x%x; trying the %d entries below it' % (image, around, len(candidates)))
    for entry in reversed(candidates):
        stream = list(MD.disasm(blob[entry - base:entry - base + 0x400], entry))
        # the call instruction must end exactly at the recorded return address
        call = next((insn for insn in stream if insn.address + insn.size == around
                     and insn.mnemonic.startswith('call')), None)
        if call is None:
            continue
        index = stream.index(call)
        arguments = []
        while index > 0 and stream[index - 1].mnemonic == 'push':
            index -= 1
            arguments.append(stream[index])
        print('  entry 0x%x  ->  call at 0x%x  %s  %s'
              % (entry, call.address, call.mnemonic, call.op_str))
        for insn in arguments:
            print('    0x%08x  push  %-24s' % (insn.address, insn.op_str))
        print('  ARGUMENTS PUSHED FOR THE CALL: %d  ->  the callee must pop %d bytes (ret %d)'
              % (len(arguments), len(arguments) * 4, len(arguments) * 4))
        return
    print('  no candidate entry makes 0x%x a return address' % around)


main()
