"""Audit the class section 121.4 named: a suite passes an address translated from the th11 fixture, and the
th12 callee derives a pointer from the register that carries it.

touch() translates addresses between the th11 fixture and the th12 runtime and does not translate structure
offsets, so a suite that hands a th11-shaped object to a th12 function walks a th11 layout against th12 code.
This tool measures the class instead of describing it: it reads the translation tables, finds every
`m.call(touch(<th11 address>), {...})` site in the suites, and disassembles the th12 target to see whether its
first instructions load a pointer FROM the register the call supplied - `mov ebx, ecx` then `mov esi, [ebx+disp]`
is the shape section 121 found at 0x004154d0.

  py -3 tools/th-derived-args.py [--image PATH] [--tests DIR]
"""
import argparse
import collections
import io
import json
import os
import re
import struct

import capstone

_ARGS = argparse.ArgumentParser()
_ARGS.add_argument('--image', default='H:/Games/th/12/th12.exe')
_ARGS.add_argument('--tests', default=os.path.join('runtimes', 'th12', 'th12_web', 'tests', 'cpp'))
_ARGS.add_argument('--trace', action='store_true')
_ARGS.add_argument('--probe', default=None, help='an address to report the derivation test for, e.g. 0x4154d0')
_OPTS = _ARGS.parse_args()

TABLES = ['oracle-th11-th12.json', 'oracle-globals-th11-th12.json', 'oracle-constants-th11-th12.json']
TABLE_DIR = os.path.join('docs', 'porting')
UNSETTLED = {'refuted', 'rejected', 'failed', 'unsettled', 'unknown', 'guess'}


def text_of(path):
    data = io.open(path, 'rb').read()
    pe = struct.unpack_from('<I', data, 0x3c)[0]
    image_base = struct.unpack_from('<I', data, pe + 0x34)[0]
    count = struct.unpack_from('<H', data, pe + 6)[0]
    header = struct.unpack_from('<H', data, pe + 20)[0]
    for index in range(count):
        offset = pe + 24 + header + index * 40
        name = data[offset:offset + 8].rstrip(b'\x00').decode('latin1')
        if name == '.text':
            virtual_size, virtual_address, raw_size, raw_pointer = struct.unpack_from('<IIII', data, offset + 8)
            # Suite addresses are virtual addresses (0x4154d0) while a section header holds an RVA. Without the
            # image base this disassembled NOTHING and the audit reported "0 of 81" - the failure mode the
            # audit exists to catch, committed by the audit itself.
            return data[raw_pointer:raw_pointer + max(virtual_size, raw_size)], image_base + virtual_address
    raise SystemExit('no .text in %s' % path)


def translations():
    mapping = {}
    for name in TABLES:
        path = os.path.join(TABLE_DIR, name)
        if not os.path.exists(path):
            continue
        document = json.load(io.open(path, encoding='utf-8'))
        for row in document.get('rows', []):
            status = str(row.get('status') or row.get('confidence') or row.get('verdict') or '').lower()
            if row.get('ready') is False or status in UNSETTLED:
                continue
            source, target = row.get('sourceAddress'), row.get('targetAddress')
            if source is None or target is None:
                continue
            try:
                mapping[int(str(source), 16)] = int(str(target), 16)
            except ValueError:
                continue
    return mapping


def supplied_registers(options):
    found = set()
    for name in ('ecx', 'edx', 'esi', 'edi', 'ebx'):
        if re.search(r'\b%s\s*:' % name, options):
            found.add(name.upper())
    if re.search(r'\bargs\s*:', options):
        found.add('STACK')
    return found


MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
MD.detail = True
blob, base = text_of(_OPTS.image)
mapping = translations()

sites = collections.defaultdict(list)
pattern = re.compile(r'm\.call\(\s*touch\(\s*(0x[0-9a-fA-F]+)\s*\)\s*(?:,\s*\{([^}]*)\})?')
for name in sorted(os.listdir(_OPTS.tests)):
    if not name.endswith('.test.mjs'):
        continue
    text = io.open(os.path.join(_OPTS.tests, name), encoding='utf-8').read()
    for match in pattern.finditer(text):
        source = int(match.group(1), 16)
        target = mapping.get(source, source)
        line = text.count('\n', 0, match.start()) + 1
        near = text.split('\n')[max(0, line - 9):line]
        # A register can be supplied by m.reg('REG', value) on a neighbouring line instead of in the call
        # options - bullet-state.test.mjs does exactly that with EDI - so a claim that a register was "never
        # supplied" is only allowed after looking at the surrounding lines.
        preset = {name.upper() for name in re.findall(r"m\.reg\(\s*'(E[A-Z]{1,2}|[A-D]X)'", '\n'.join(near))}
        sites[target].append((name, source, supplied_registers(match.group(2) or ''), preset, line))


def derives(entry, registers):
    """Does the body reach a memory operand whose base is a supplied register, through copies?

    Section 121's shape is `mov ebx, ecx` then `mov esi, [ebx+0x174c]`: the base is a COPY of the supplied
    register, so matching the supplied name directly finds nothing. The alias set follows `mov rA, rB` copies.
    """
    stream = []
    for insn in MD.disasm(blob[entry - base:entry - base + 400], entry):
        stream.append(insn)
        if len(stream) >= 40:
            break
    aliases = {name: name for name in registers}
    for index, insn in enumerate(stream):
        if insn.mnemonic == 'mov' and len(insn.operands) == 2:
            left, right = insn.operands
            if left.type == capstone.x86.X86_OP_REG and right.type == capstone.x86.X86_OP_REG:
                target_reg = insn.reg_name(left.reg).upper()
                source_reg = insn.reg_name(right.reg).upper()
                if source_reg in aliases:
                    aliases[target_reg] = aliases[source_reg]
                else:
                    aliases.pop(target_reg, None)
        if insn.mnemonic != 'mov' or len(insn.operands) != 2:
            continue
        left, right = insn.operands
        if left.type != capstone.x86.X86_OP_REG or right.type != capstone.x86.X86_OP_MEM:
            continue
        base_name = insn.reg_name(right.mem.base)
        if base_name is None:  # absolute addressing carries no base register
            continue
        base_name = base_name.upper()
        if base_name in aliases:
            detail = '%s ; %s %s' % ('0x%08x' % stream[max(0, index - 1)].address, insn.mnemonic, insn.op_str)
            return (detail, aliases[base_name], base_name, right.mem.disp)
    return (None, None, None, None)


print('  translation rows: %d;  call sites through touch(): %d targets, %d sites'
      % (len(mapping), len(sites), sum(len(v) for v in sites.values())))
deriving, plain = [], []
for target, items in sorted(sites.items()):
    registers = set()
    for _, _, found, _, _ in items:
        registers |= found
    detail, origin, base_reg, disp = (derives(target, registers)
                                     if target >= 0x10000 and registers - {'STACK'} else (None, None, None, None))
    (deriving if detail else plain).append((target, items, detail, origin, base_reg, disp))

print('  targets whose body DERIVES a pointer from a supplied register: %d' % len(deriving))
for target, items, detail, origin, base_reg, disp in deriving:
    where = sorted({('%s:%d' % (name.replace('.test.mjs', '')[:22], line)) for name, _, _, _, line in items})
    print('    0x%08x  %-30s base=%-4s<-%-4s disp=%+#x  %s'
          % (target, ','.join(sorted({n.replace('.test.mjs', '')[:20] for n, _, _, _, _ in items}))[:30],
             base_reg, origin, disp, detail))
    print('        sites: %s%s' % (', '.join(where[:6]), ' ...' if len(where) > 6 else ''))
print('  targets whose body shows no derivation in its first 40 instructions: %d' % len(plain))
print('  NOTE: every derivation above was found THROUGH a supplied register, so the base is supplied by')
print('  construction - a report of "never supplied" would be an artifact. What each site still needs is an')
print('  object whose field at disp holds a th12-shaped pointer, and that is measured per site, not read here.')
if _OPTS.probe:
    probe = int(_OPTS.probe, 16)
    print('  probe 0x%08x: in the call-site set: %s' % (probe, probe in sites))
    print('    sites: %s' % ([(name, '0x%x' % src, sorted(regs), sorted(preset), line)
                            for name, src, regs, preset, line in sites.get(probe, [])][:6],))
    print('    derivation with ECX: %s' % (derives(probe, {'ECX'}),))
    if _OPTS.trace:
        print('    first instructions from the entry:')
        for insn in list(MD.disasm(blob[probe - base:probe - base + 400], probe))[:26]:
            print('      0x%08x  %-10s %s' % (insn.address, insn.mnemonic, insn.op_str))
