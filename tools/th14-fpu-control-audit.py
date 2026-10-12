"""Read-only retail x87 control instruction/call-site inventory.

Linear decoding is an inventory, not a reachability or live-game proof.
"""
import hashlib, importlib, json
from pathlib import Path
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/th14/fpu-control-audit'
OUT.mkdir(parents=True, exist_ok=True)
sha = lambda b: hashlib.sha256(b).hexdigest()

def main():
    image = importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
    assert sha(image.data) == 'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    decoder = Cs(CS_ARCH_X86, CS_MODE_32)
    decoder.skipdata = True
    text = next(s for s in image.sections if s[0] == '.text')
    instructions = list(decoder.disasm(image.read(text[1], text[4]), text[1]))
    controls = []
    for i, ins in enumerate(instructions):
        if ins.mnemonic not in ('fldcw', 'fninit', 'finit', 'fnstcw', 'fstcw', 'ldmxcsr'):
            continue
        controls.append(dict(address=hex(ins.address), mnemonic=ins.mnemonic,
                             operands=ins.op_str,
                             context=[f'{x.address:08x} {x.mnemonic} {x.op_str}'
                                      for x in instructions[max(0, i-24):i+12]]))
    targets = {0x403470, 0x4034b0, 0x4034f0, 0x41cb70, 0x432100,
               0x435ab0, 0x47d230, 0x46b110}
    call_sites = {hex(t): [] for t in targets}
    for ins in instructions:
        if ins.mnemonic != 'call' or not ins.op_str.startswith('0x'):
            continue
        target = int(ins.op_str, 16)
        if target in targets:
            call_sites[hex(target)].append(hex(ins.address))
    report = dict(executableSha256=sha(image.data), toolSha256=sha(Path(__file__).read_bytes()),
                  instructionCount=len(instructions), controls=controls,
                  directCallSites=call_sites,
                  scope='Linear retail .text decoding only; call graph/reachability and live thread FPU state not established.')
    (OUT / 'inventory.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(instructions=len(instructions), controls=[{k:r[k] for k in ('address','mnemonic','operands')} for r in controls])))

if __name__ == '__main__':
    main()
