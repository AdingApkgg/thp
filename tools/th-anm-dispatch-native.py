"""Execute the newer retail ANM dispatcher, including its special opcode 300."""
import hashlib, importlib, json
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EIP
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = Path(__file__).resolve().parents[1]

def main():
    reports = []
    for title in (16, 17, 18):
        img, table, default = importlib.import_module('th-anm-handlers').handlers(title)
        # Unique cmp-300 / signed-greater / equality / increment / low guard.
        candidates = []
        for _, base, size, raw, count in img.sections:
            data = img.data[raw:raw+count]
            off = 0
            while True:
                off = data.find(bytes.fromhex('3d2c0100000f8f'), off)
                if off < 0: break
                if data[off+11:off+13] == bytes.fromhex('0f84') and data[off+17:off+23] == bytes.fromhex('403dd6000000'):
                    candidates.append(base+off)
                off += 1
        assert len(candidates) == 1, (title, candidates)
        entry = candidates[0]
        md = Cs(CS_ARCH_X86, CS_MODE_32)
        first = list(md.disasm(img.read(entry, 43), entry))
        second_entry = int(first[1].op_str, 16)
        second = list(md.disasm(img.read(second_entry, 30), second_entry))
        dispatch = {i.address for i in first + second}
        m = Uc(UC_ARCH_X86, UC_MODE_32)
        for _, base, size, raw, count in img.sections:
            start = base & ~4095
            m.mem_map(start, ((base+size+4095)&~4095)-start)
            m.mem_write(base, img.data[raw:raw+count])
        rows = []
        for op in list(range(-3, 651)) + [-32768, 32767]:
            m.reg_write(UC_X86_REG_EAX, op & 0xffffffff)
            at = entry
            for _ in range(20):
                assert at in dispatch, (title, op, hex(at))
                m.emu_start(at, 0, count=1)
                at = m.reg_read(UC_X86_REG_EIP)
                if at not in dispatch: break
            else: raise AssertionError('dispatcher did not leave bounded instructions')
            assert at == table.get(op, default), (title, op, hex(at), hex(table.get(op, default)))
            rows.append(dict(opcode=op, handler=hex(at)))
        reports.append(dict(title=title, executableSha256=hashlib.sha256(img.data).hexdigest(), entry=hex(entry), cases=len(rows), passed=True, rows=rows))
    out = ROOT/'docs/porting/anm-dispatch-16-18-verified.json'
    out.write_text(json.dumps(dict(scope='Retail signed opcode dispatch only, before executing any handler. All gaps and both band guards are executed; no handler semantics or gameplay claim.', reports=reports, toolHashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ('tools/th-anm-handlers.py', 'tools/th-anm-dispatch-native.py')}), indent=2)+'\n', encoding='utf-8')
    print('PASS native ANM dispatch: '+', '.join(f'TH{r["title"]}: {r["cases"]} cases' for r in reports))

if __name__ == '__main__': main()
