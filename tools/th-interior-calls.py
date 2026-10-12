"""Derive, from the original image, the stack frame a suite must supply when it calls a function's interior.

Section 95 measured the class: a suite that enters a function at a jump-table label skips the prologue,
and the shared epilogue then pops registers nobody pushed, so `ret` reads a caller slot as the return
address. Fifty-four of th12's hundred and sixteen literal interior call sites are in that state. The
repair is not to hand-write stack arithmetic in thirty-six suites: the image already says what the
epilogue pops, so the machine can rebuild the skipped frame. This tool computes that frame and writes
docs/porting/oracle-interior-calls.json, which the harness hands to the machine.

Three facts are derived per call target, and each was found by measurement rather than by reading:

* `slots` / `saves` - the epilogue's contiguous pops before the LAST `ret` in the block (section 96). The
  first rule summed every pop in the block and reported six slots for 0x44acd0 where the shared epilogue
  pops three.
* `frame.setsEbp` / `frame.usesEbp` - whether the prologue before the label loads EBP and whether the body
  reads or writes [ebp+disp] (section 100). Round 307 had refuted a blanket EBP default over every call.
* `frame.stack` - the whole net ESP change the prologue made, `4 * pushes + sum(sub esp, imm) - 4 * slots`,
  because the epilogue undoes it and entering at the label leaves ESP that much too high (section 101).
  Measured on 0x432cc0: returnDrift 34 words at the fault plus the one the `ret` popped is 35 words = 0x8c,
  while the subtractions alone accounted for 27 - the missing 32 bytes are the skipped pushes.

`call_targets` returns PADDING entries as well (section 91: 0x46022b decodes as `mov dh,bh`), and treating
those as function entries kept 0x432cc0 - a label the suites really call - out of the map, so the entry set
here is the set a direct `E8` call reaches.

  py -3 tools/th-interior-calls.py --title th12 --write
"""
import argparse
import importlib.util
import io
import json
import os
import re
import struct

import capstone

_ARGS = argparse.ArgumentParser()
_ARGS.add_argument('--title', default='th12')
_ARGS.add_argument('--image', default=None)
_ARGS.add_argument('--tests', default=None)
_ARGS.add_argument('--write', action='store_true')
_ARGS.add_argument('--audit', action='store_true')
_OPTS = _ARGS.parse_args()

IMAGE = _OPTS.image or 'H:/Games/th/12/th12.exe'
TESTS = _OPTS.tests or os.path.join('runtimes', 'th12', 'th12_web', 'tests', 'cpp')
OUT = 'docs/porting/oracle-interior-calls.json'
MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
MD.detail = True

_spec = importlib.util.spec_from_file_location('tb', os.path.join('tools', 'th-twin-batch.py'))
batch = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(batch)

POPPED = ('pop', 'popal', 'popad', 'popfd', 'popf')


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


def direct_calls(blob, base):
    """Addresses that some `E8` displacement calls, i.e. real function entries."""
    found = set()
    for offset in range(0, len(blob) - 5):
        if blob[offset] == 0xe8:
            caller = base + offset
            found.add((caller + 5 + struct.unpack_from('<i', blob, offset + 1)[0]) & 0xffffffff)
    return found


def block_end(blob, base, entry):
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


def epilogue_pops(inside):
    """The registers the epilogue pops, found by walking BACK from the last `ret`.

    Section 96 counted only the contiguous run of pops immediately before the `ret`, and section 101.2 found
    the epilogue that rule cannot see: `mov ecx,[esp+0x70]; pop edi; pop ebp; xor ecx,esp; call
    __security_check_cookie; add esp,0x6c; ret 4` - the pops are separated from the return by the /GS cookie
    check and the frame release, so the contiguous run is empty and the row's slots came out zero. With too
    few slots the epilogue pops the machine's planted return address into a register, which is how
    `enemy-frame` ended up with EDI holding 0x7f00000 - a 1:1 fidelity defect, since the real prologue would
    have pushed that register with its own value. The walk therefore skips the instructions that are part of
    the epilogue without touching the register stack (the release, the cookie check, moves, compares) and
    stops at anything that ends the path: a `push`, another `ret`, or a branch, because the earlier returns of
    a function belong to paths this label does not take.
    """
    pops, saves = 0, []
    started = False
    for insn in reversed(inside):
        mnemonic = insn.mnemonic
        operands = insn.op_str.replace(' ', '').lower()
        if mnemonic == 'ret':
            # The first `ret` is where the walk starts. A SECOND one ends it: functions hold several
            # returns and the pops before an earlier return belong to a path this label does not take.
            # Missing that produced duplicates - 0x432cc0 was given 'esi ebx edi ebp esi ebx edi ebp' -
            # which is over-counting, and over-counting is not safe either: every extra slot moves ESP
            # down, so the entered code's [esp+disp] reads shift to a different word.
            if started:
                break
            started = True
            continue
        if mnemonic in POPPED:
            pops += 1
            saves.append(insn.op_str.strip())
        elif mnemonic.startswith('push'):
            break
        elif mnemonic in ('add', 'sub', 'lea') and operands.startswith('esp'):
            continue
        elif mnemonic in ('mov', 'xor', 'and', 'or', 'test', 'cmp', 'call', 'nop', 'movzx', 'movsx'):
            continue
        else:
            break
    return pops, list(reversed(saves))


def prologue_cost(head):
    """The net ESP change the prologue made: bytes pushed, plus bytes subtracted."""
    pushes, stack = 0, 0
    for insn in head:
        operands = insn.op_str.replace(' ', '').lower()
        if insn.mnemonic.startswith('push'):
            pushes += 1
        if insn.mnemonic == 'sub' and operands.startswith('esp,') and insn.operands:
            last = insn.operands[-1]
            if last.type == capstone.x86.X86_OP_IMM:
                stack += last.imm
        elif insn.mnemonic == 'lea' and operands.startswith('esp,[esp') and ']' in operands:
            tail = operands[operands.index('-'):operands.index(']')] if '-' in operands else ''
            if tail[1:].isdigit():
                stack += int(tail[1:])
    return pushes, stack


def balance_at_label(head):
    """The ESP offset at the label, in bytes, along the straight line that dispatches to it.

    Section 101 probed the amount this entry needs at 136 bytes and measured that it is 0x6c (the epilogue's
    own release, which the image states) plus 28 bytes. What the machine has to pre-apply is the whole ESP
    offset the prefix leaves in place when the label starts running - every push and `sub esp` it made that
    the entered code will only later undo - so the quantity is the balance at the label, and this computes it
    by walking the prefix in order, accumulating pushes down and pops/sub/add up, and stopping at the
    dispatch: an unconditional jump or an indirect table jump. Conditional branches either leave the prefix
    or fall through, so they do not stop the walk; a `call` is balanced in itself and contributes nothing.
    """
    delta = 0
    for insn in head:
        mnemonic = insn.mnemonic
        operands = insn.op_str.replace(' ', '').lower()
        if mnemonic.startswith('push'):
            delta -= 4
        elif mnemonic in POPPED:
            delta += 4
        elif mnemonic == 'sub' and operands.startswith('esp,') and insn.operands:
            last = insn.operands[-1]
            if last.type == capstone.x86.X86_OP_IMM:
                delta -= last.imm
        elif mnemonic == 'add' and operands.startswith('esp,') and insn.operands:
            last = insn.operands[-1]
            if last.type == capstone.x86.X86_OP_IMM:
                delta += last.imm
        elif mnemonic == 'lea' and operands.startswith('esp,[esp') and ']' in operands:
            if '+' in operands:
                tail = operands[operands.index('+'):operands.index(']')]
                if tail[1:].isdigit():
                    delta += int(tail[1:])
            elif '-' in operands:
                tail = operands[operands.index('-'):operands.index(']')]
                if tail[1:].isdigit():
                    delta -= int(tail[1:])
        elif mnemonic == 'jmp':
            # The dispatch. An indirect jump is the jump table; a direct one is the tail of the chain.
            if operands.startswith('dwordptr[') or 'ptr[' in operands or operands[0] == '0':
                break
            break
    return delta


PADDING_RUN = 8


def body_end(blob, base, address, limit=4096):
    """The end of the body entered at `address`: the first run of padding after it.

    Section 279 measured the extent taken to the next call target running past the function own padding
    (0x00432cc0 reported 387 `ret`s, 0x00451ef0 799). The body of the entered code ends where the padding
    between bodies begins, and that is a run of `int3`s in this image.
    """
    run = 0
    for off in range(limit):
        byte = blob[address - base + off]
        if byte in (0xCC, 0x90):
            run += 1
            if run >= PADDING_RUN:
                return address + off + 1 - run
        else:
            run = 0
    return address + limit


def reachable_ret(blob, base, address, lo=None, hi=None, budget=40000, table_cap=96):
    """The nearest `ret` in the entered code, by instruction distance, and what its own `ret` pops.

    Section 280-281: distance chooses the exit; and a body that ends in `jmp dword ptr [reg*4 + table]`
    has no static exit at all until the table is read. The table sits in the image, so its entries are
    edges like any other: this adds every in-section entry of such a table, in table order, behind the
    fall-through and any direct target.
    """

    def table_targets(insn):
        if insn.mnemonic != 'jmp' or not insn.operands:
            return []
        operand = insn.operands[0]
        if operand.type != capstone.x86.X86_OP_MEM:
            return []
        disp = operand.mem.disp
        if not (base <= disp < base + len(blob)):
            return []
        out = []
        for index in range(table_cap):
            if disp - base + index * 4 + 4 > len(blob):
                break
            value = struct.unpack_from('<I', blob, disp - base + index * 4)[0]
            if not (base <= value < base + len(blob)):
                break
            out.append(value)
        return out

    def ok(va):
        return (lo is None or va >= lo) and (hi is None or va <= hi)

    from collections import deque

    if not ok(address):
        return None
    seen, queue, steps = {address}, deque([(address, 0)]), 0
    while queue and steps < budget:
        va, distance = queue.popleft()
        steps += 1
        insns = list(MD.disasm(blob[va - base:va - base + 16], va))
        if not insns:
            continue
        insn = insns[0]
        if insn.mnemonic == 'ret':
            return (insn.address, insn.operands[0].imm if insn.operands else 0, distance)
        following = [insn.address + insn.size]
        if (insn.mnemonic.startswith('j') and insn.operands
                and insn.operands[0].type == capstone.x86.X86_OP_IMM):
            following.append(insn.operands[0].imm)
        following.extend(table_targets(insn))
        for step in following:
            if ok(step) and step not in seen:
                seen.add(step)
                queue.append((step, distance + 1))
    return None


def forward_to_ret(inside):
    """The ESP the entered code itself moves between the label and the `ret` it reaches, in bytes.

    Section 101's probe fixed what 0x432cc0 needs at 136 bytes while the prefix balance says 124, so the
    missing 12 are on this side of the label. The `ret` reads the word at ESP, so if the entered code moves
    ESP by this much before reaching it, entering with ESP that much BELOW the return address puts the
    return address under the `ret` - which is the reserve, measured from the code that actually runs rather
    than from the prefix that was skipped.
    """
    delta = 0
    for insn in inside:
        mnemonic = insn.mnemonic
        operands = insn.op_str.replace(' ', '').lower()
        if mnemonic == 'ret':
            break
        if mnemonic.startswith('push'):
            delta -= 4
        elif mnemonic in POPPED:
            delta += 4
        elif mnemonic == 'sub' and operands.startswith('esp,') and insn.operands:
            last = insn.operands[-1]
            if last.type == capstone.x86.X86_OP_IMM:
                delta -= last.imm
        elif mnemonic == 'add' and operands.startswith('esp,') and insn.operands:
            last = insn.operands[-1]
            if last.type == capstone.x86.X86_OP_IMM:
                delta += last.imm
        elif mnemonic == 'lea' and operands.startswith('esp,[esp') and ']' in operands:
            if '+' in operands:
                tail = operands[operands.index('+'):operands.index(']')]
                if tail[1:].isdigit():
                    delta += int(tail[1:])
            elif '-' in operands:
                tail = operands[operands.index('-'):operands.index(']')]
                if tail[1:].isdigit():
                    delta -= int(tail[1:])
    return delta


def audit(blob, base, entries, real, entry_set, rows):
    """Why a suite-called address has no row, asked of this tool's own criteria.

    Section 334 read the committed verdict's entry column and found 27 of the 60 entries the trapping suites
    reach absent from the map. Absence is only a gap if the address is one the interior machinery is supposed
    to cover, and only this tool's own two filters can say: an address that is a direct-call target is a real
    entry - entering it runs its own prologue, so no row is needed - and an address with no enclosing real
    entry cannot be given one. Everything else is a row that should exist and does not.
    """
    pattern = re.compile(r'm\.call\(\s*(0x[0-9a-fA-F]+)')
    called = {}
    for name in sorted(os.listdir(TESTS)):
        if not name.endswith('.test.mjs'):
            continue
        text = io.open(os.path.join(TESTS, name), encoding='utf-8').read()
        for match in pattern.finditer(text):
            address = int(match.group(1), 16)
            called.setdefault(address, []).append(name.replace('.test.mjs', ''))
    enclosing = sorted(entry_set)
    real_entry, no_enclosing, should_have_row, covered = [], [], [], []
    for address, suites in sorted(called.items()):
        key = '0x%08x' % address
        if key in rows:
            covered.append((key, suites))
        elif address in real:
            real_entry.append((key, suites))
        elif max((candidate for candidate in enclosing if candidate <= address), default=None) is None:
            no_enclosing.append((key, suites))
        else:
            should_have_row.append((key, suites))
    print('  suite-called addresses: %d' % len(called))
    print('  covered by a row:        %d' % len(covered))
    print('  real entries (no row needed): %d' % len(real_entry))
    print('  below every known entry (no row possible): %d' % len(no_enclosing))
    print('  SHOULD have a row and does not: %d' % len(should_have_row))
    for label, items in (('real entry', real_entry), ('no enclosing', no_enclosing),
                         ('missing row', should_have_row)):
        for key, suites in items[:8]:
            print('    %-12s %s  (%s)' % (label, key, ', '.join(sorted(set(suites))[:3])))
    return should_have_row


def main():
    blob, base = text_of(IMAGE)
    entries = sorted(batch.call_targets(MD, blob, base))
    real = direct_calls(blob, base)
    entry_set = {address for address in entries if address in real}
    enclosing = sorted(entry_set)
    pattern = re.compile(r'm\.call\(\s*(0x[0-9a-fA-F]+)')
    rows = {}
    for name in sorted(os.listdir(TESTS)):
        if not name.endswith('.test.mjs'):
            continue
        text = io.open(os.path.join(TESTS, name), encoding='utf-8').read()
        for match in pattern.finditer(text):
            address = int(match.group(1), 16)
            if address in entry_set:
                continue
            line = text[:match.start()].count('\n') + 1
            entry = max((candidate for candidate in enclosing if candidate <= address), default=None)
            if entry is None:
                continue
            key = '0x%08x' % address
            row = rows.setdefault(key, {'entry': '0x%08x' % entry, 'slots': 0, 'saves': [],
                                        'balance': 0, 'from': [], 'frame': {}})
            row['from'].append('%s L%d' % (name, line))
            # Section 278/279: the fields of a label past the enclosing function first body were derived from an
            # empty instruction list; the extent is the label own body, clipped to the next call target, and
            # never below the label itself, while the lookup that reaches an exit may go backwards to it.
            end = min(min([e for e in sorted(entries) if e > entry] or [block_end(blob, base, entry)]),
                      max(body_end(blob, base, address), address + 16))
            stream = list(MD.disasm(blob[entry - base:end], entry))
            inside = [insn for insn in stream if insn.address >= address]
            head = [insn for insn in stream if insn.address < address]

            # The count is the epilogue, not the whole remainder: a function can hold several returns, and
            # summing every pop in the block reported six slots for 0x44acd0 where the shared epilogue pops
            # three. The epilogue is the contiguous run of pops immediately before a `ret`, and the one a
            # label reaches is the last in the block - the earlier ones belong to branches the entered code
            # does not take (0x44acd0 reaches 0x44ae98 through `jnp`).
            returns = [index for index, insn in enumerate(inside) if insn.mnemonic == 'ret']
            slots, saves = 0, []
            contiguous = 0
            if returns:
                last = returns[-1]
                start = last - 1
                while start >= 0 and inside[start].mnemonic in POPPED:
                    start -= 1
                contiguous = last - 1 - start
                slots, saves = epilogue_pops(inside[:last + 1])

            sets = any(insn.mnemonic == 'mov' and insn.op_str.replace(' ', '') == 'ebp,esp'
                       for insn in head)
            uses, displacements, outliers = False, [], 0
            for insn in inside:
                for operand in insn.operands:
                    if operand.type != capstone.x86.X86_OP_MEM or operand.mem.base != capstone.x86.X86_REG_EBP:
                        continue
                    uses = True
                    # A frame offset is small. The sweep can run past the end of a function into data, and
                    # 0x00416ee0 showed offsets of -2050752447 and 2130723197, which are decoded garbage
                    # rather than a frame: counting those would make the frame claim nonsense.
                    if -0x1000 <= operand.mem.disp <= 0x10000:
                        displacements.append(operand.mem.disp)
                    else:
                        outliers += 1

            pushes, stack = prologue_cost(head)
            at_label = balance_at_label(head)
            # Section 101's probe fixed the amount this entry needs at 136 bytes and measured that the
            # prefix sum (176) is wrong because it counts pushes the prefix itself pops. The quantity the
            # machine has to pre-apply is the balance at the label, so the reserve is its negated offset and
            # the prefix sum is kept only as the provenance of the rule that was refuted.
            reserve = max(0, -at_label)

            # Section 280: the upper bound of the walk was an assumption (the next call targets), and it hid the

            # two rows whose exit had been read by hand. The flow gives no upper bound; distance gives the choice.

            reached = reachable_ret(blob, base, address, lo=entry) or (0, 0, 0)
            row['balance'] = slots
            row['slots'] = slots
            row['saves'] = saves
            row['contiguous'] = contiguous
            row['frame'] = {'setsEbp': bool(sets), 'usesEbp': bool(uses),
                            'maxDisp': max(displacements) if displacements else 0,
                            'minDisp': min(displacements) if displacements else 0,
                            'stack': reserve, 'atLabel': at_label, 'prefix': 4 * pushes + stack - 4 * slots,
                            'forward': forward_to_ret(inside), 'sub': stack, 'pushes': pushes,
                            'rets': ['0x%08x' % insn.address for insn in inside if insn.mnemonic == 'ret'],
        'retImm': reached[1], 'reachedRet': '0x%08x' % reached[0], 'reachedDist': reached[2],
                            'outliers': outliers, 'prologue': len(head)}

    unbalanced = [row for row in rows.values() if row['slots'] > 0]
    framed = [row for row in rows.values() if row['frame']['usesEbp'] and not row['frame']['setsEbp']]
    reserved = [row for row in rows.values() if row['frame']['stack'] > 0]
    print('  %s: %d interior call targets, %d with slots to supply, %d needing a frame the prologue would '
          'have set, %d needing the prologue stack' % (IMAGE, len(rows), len(unbalanced), len(framed),
                                                       len(reserved)))
    for key in sorted(rows):
        row = rows[key]
        if row['frame']['stack'] > 0:
            print('    %s entry %s  reserve %d (pushes %d, sub %d, slots %d)'
                  % (key, row['entry'], row['frame']['stack'], row['frame']['pushes'],
                     row['frame']['sub'], row['slots']))
    if _OPTS.write:
        document = {
            'title': _OPTS.title,
            'image': IMAGE,
            'method': ('slots = the epilogue pops before the last ret, in pop order, rebuilt by the harness; '
                       'frame.setsEbp/usesEbp = whether the prologue before the label loads EBP and whether '
                       'the body uses [ebp+disp]; frame.stack = 4*pushes + sub esp - 4*slots, the net ESP the '
                       'prologue changed and the epilogue undoes'),
            'rows': rows,
        }
        io.open(OUT, 'w', encoding='utf-8', newline='\n').write(
            json.dumps(document, ensure_ascii=False, indent=1, sort_keys=True) + '\n')
        print('  wrote %s (%d targets)' % (OUT, len(rows)))
    if _OPTS.audit:
        audit(blob, base, entries, real, entry_set, rows)


main()
