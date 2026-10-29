"""Freeze a bounded Scene-copy observer with stopped main-thread context.

This adds reads to existing debug events. It does not add breakpoints, alter
instructions, control thread scheduling, or supply observations to the game.
"""
from pathlib import Path
import argparse
import ast
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda data: hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'artifacts/th14') and not out.exists()
    base = ROOT / 'tools/th14-native-campaign-observer-oct25.py'
    raw = base.read_bytes()
    source = raw.decode().replace('\r\n', '\n')
    patches = []

    def replace(old, new, label):
        nonlocal source
        assert source.count(old) == 1, label
        source = source.replace(old, new)
        patches.append(label)

    replace('root=Path(__file__).resolve().parents[1]',
            'root=Path(' + repr(str(ROOT)) + ')', 'privateWorkspaceRoot')
    needle = '        if pc==0x40d435:\n'
    code = '''        if pc in (0x40d435,0x40d447):
            assert tid!=pi.tid
            main=context(threads[pi.tid])
            regs=dict(zip(['edi','esi','ebx','edx','ecx','eax','ebp','eip','cs','eflags','esp'],struct.unpack_from('<11I',main,156)))
            stack_count=min(64,0x1000-(regs['esp']&0xfff))
            row.update(mainThreadStoppedContext=dict(registers=regs,
                debugRegisters=dict(zip(['dr0','dr1','dr2','dr3','dr6','dr7'],struct.unpack_from('<6I',main,4))),
                stackHex=read(regs['esp'],stack_count).hex(),
                instructionHex=read(regs['eip'],min(8,0x1000-(regs['eip']&0xfff))).hex()),
                sampledAfterDebugStopNotSimultaneous=True,
                explicitThreadSchedulingControl=False,nativeValuesProvidedToEngine=False)
''' + needle
    replace(needle, code, 'mainContextAtExistingSceneEdges')
    replace('diagnosticPrefixOnly=False,asciiBeginObserved',
            'diagnosticPrefixOnly=True,asciiBeginObserved', 'finitePrefixScope')
    replace("    (home/'report.json').write_text",
            "    report.update(sceneCopyMainStoppedContext=True,additionalBreakpointCount=0,explicitThreadSchedulingControl=False,diagnosticStopReason='maximumCallbacks'if callback_count>=opt.maximum_callbacks else 'naturalEnd'if complete else 'errorOrBudget',fullReplayAccepted=False)\n    (home/'report.json').write_text",
            'explicitReportScope')
    replace('if error or not complete:raise SystemExit(1)',
            'if error or (not complete and callback_count<opt.maximum_callbacks):raise SystemExit(1)',
            'declaredPrefixExit')
    ast.parse(source)
    out.mkdir(parents=True)
    encoded = source.encode()
    (out / 'observer.py').write_bytes(encoded)
    receipt = dict(baseObserverPath=base.relative_to(ROOT).as_posix(),
                   baseObserverSha256=SHA(raw), generatedObserverSha256=SHA(encoded),
                   preparerSha256=SHA(Path(__file__).read_bytes()),
                   exactCompositionSteps=patches, originalProcessLaunched=False,
                   additionalBreakpoints=0, explicitThreadSchedulingControl=False,
                   originalInstructionsChanged=False, nativeValuesProvidedToEngine=False,
                   sampledAfterDebugStopNotSimultaneous=True,
                   completeGame=False, nativeEquivalent=False)
    (out / 'prepared.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
