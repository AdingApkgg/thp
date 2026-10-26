"""Compare the actual ReplayStageState C++ body with native worker controls.

The initial GameSession call contract is checked in source, not represented as
a compiled whole-GameSession or ordinary-menu test. Full integration is separate.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import struct
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['native','decoded','output']:parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();out=args.output.resolve();assert out.is_relative_to(ROOT/'artifacts/th14')and not out.exists();out.mkdir(parents=True)
    native_raw=args.native.read_bytes();native=json.loads(native_raw);assert native['completed']and native['caseCount']==288
    decoded=args.decoded.read_bytes();assert SHA(decoded)==native['decodedSha256'];headers={};offset=0x94
    for _ in range(struct.unpack_from('<I',decoded,0x78)[0]):
        stage=struct.unpack_from('<H',decoded,offset)[0];headers[stage]=decoded[offset:offset+0xdc]
        offset+=0xdc+struct.unpack_from('<I',decoded,offset+8)[0]
    game=ROOT/'runtimes/th12/th12_web/cpp/game';session=(game/'GameSession.cpp').read_text();old='entry.restore(economy,gameplay_rng,true,kPortTitle==14?&animations.script_rng:nullptr);'
    new='entry.restore(economy,gameplay_rng,kPortTitle==14?state.demo:true,kPortTitle==14?&animations.script_rng:nullptr);'
    assert session.count(old)+session.count(new)==1;legacy=old in session
    bindings={};fixture=ROOT/'runtimes/th12/th12_web/tests/cpp/th14-initial-replay-restore-fixture.cpp'
    def bind(path):
        key=path.relative_to(ROOT).as_posix()
        if key in bindings:return
        raw=path.read_bytes();bindings[key]=dict(bytes=len(raw),sha256=SHA(raw))
        for include in re.findall(r'^\s*#\s*include\s*"([^"]+)"',raw.decode(),re.M):
            child=next((p for p in [path.parent/include,game/include]if p.exists()),None);assert child,include;bind(child.resolve())
    for path in [fixture,game/'Replay.cpp',game/'GameSession.cpp']:bind(path)
    compiler=ROOT/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
    flags=['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-g0','-ffp-contract=off','-fno-strict-aliasing','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,--allow-undefined','-I'+str(game)]
    result=subprocess.run([str(compiler),*flags,str(fixture),str(game/'Replay.cpp'),'-o',str(out/'probe.wasm')],capture_output=True,env={**os.environ,'TEMP':str(out),'TMP':str(out),'TMPDIR':str(out)})
    (out/'compile.log').write_bytes(result.stdout+result.stderr);assert result.returncode==0,result.stderr
    sys.path.insert(0,str(ROOT/'tools/tmp/th14-native-gles-python/site'));import wasmtime as W
    engine=W.Engine();wasm=(out/'probe.wasm').read_bytes();module=W.Module(engine,wasm);assert not list(module.imports)
    store=W.Store(engine);api=W.Instance(store,module,[]).exports(store);api['_initialize'](store);memory=api['memory'];pointer=api['probe_header'](store)
    rows=[];selected=[2,3,5,6,8,9,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26]
    for case in native['cases']:
        header=headers[case['stage']];memory.write(store,header,pointer)
        result=api['probe_restore'](store,pointer,int(legacy),case['initialScriptSeed'],case['initialGameSeed'],case['initialCalls'])
        actual=list(struct.unpack('<26I',memory.read(store,result,result+104)));globals_=struct.unpack_from('<28I',header,0x14)
        expected=case['rngWords']+[globals_[i]for i in selected]
        rows.append(dict(stage=case['stage'],seed=case['seed'],flags=case['flags'],initialScriptSeed=case['initialScriptSeed'],
            initialGameSeed=case['initialGameSeed'],initialCalls=case['initialCalls'],actual=actual,expected=expected,equal=actual==expected))
    report=dict(schema='th14/initial-replay-restore-comparison/1',caseCount=len(rows),exactCases=sum(r['equal']for r in rows),rows=rows,
        legacyInitialCallContract=legacy,actualRestoreBodyCompiled=True,currentGameSessionCompiled=False,callContractReadFromCurrentSource=True,
        rngWordsComparedPerCase=4,selectedEconomyWordsComparedPerCase=22,nativeReportSha256=SHA(native_raw),wasmSha256=SHA(wasm),
        compilerSha256=SHA(compiler.read_bytes()),sourceBindings=bindings,flags=flags,toolSha256=SHA(Path(__file__).read_bytes()),
        ordinaryMenuInitializationAccepted=False,completeGame=False,nativeEquivalent=False)
    (out/'comparison.json').write_text(json.dumps(report,indent=2)+'\n');(out/'run-tool.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps({k:report[k]for k in ['caseCount','exactCases','legacyInitialCallContract','actualRestoreBodyCompiled','currentGameSessionCompiled']}),flush=True)
    assert all(r['equal']for r in rows),'Actual initial restore call contract differs from the ordinary native worker'


if __name__=='__main__':main()
