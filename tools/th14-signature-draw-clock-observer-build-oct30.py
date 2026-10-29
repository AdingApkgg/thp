"""Link a diagnostic startup draw-clock input to immutable production objects."""
from pathlib import Path
import argparse, hashlib, json, os, subprocess

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda raw: hashlib.sha256(raw).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--core-build', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); out = a.output.resolve()
    assert out.is_relative_to(ROOT / 'artifacts/th14') and not out.exists()
    core_raw = a.core_build.resolve(strict=True).read_bytes(); core = json.loads(core_raw)
    assert core['compiled'] and len(core['objectBindings']) == 141
    for row in core['objectBindings']:
        assert SHA(Path(row['path']).read_bytes()) == row['sha256']
    headers = ROOT / 'runtimes/th12'
    for name, digest in core['headerHashes'].items():
        assert SHA((headers / name).read_bytes()) == digest
    out.mkdir(parents=True); fixture = out / 'fixture'; fixture.mkdir()
    source = ROOT / 'runtimes/th12/th12_web/tests/cpp'
    bindings = {}
    for name in ['th14-vm-return-worker-fixture.cpp', 'th14-normal-worker-fixture.cpp', 'th14-native-campaign-fixture.cpp']:
        raw = (source / name).read_bytes(); bindings[name] = SHA(raw)
        if name == 'th14-native-campaign-fixture.cpp':
            s = raw.decode().replace('\r\n', '\n')
            before = 'struct ColdEntryEffects final:StageResourceEffects {'
            assert s.count(before) == 1
            s = s.replace(before, '''static u32 startup_draw_frame=0,startup_draw_target=0,startup_draw_delivered=0;
static u64 startup_draw_clock=0;
static bool startup_draw_failed=false;
API(observed_startup_draw_clock) u32 observed_startup_draw_clock(u32 frame,u64 now){
    if(startup_draw_target||startup_draw_frame||!frame||now<probe_clock_ns)return 0;
    startup_draw_target=frame;startup_draw_clock=now;return 1;
}
API(observed_startup_draw_clock_state) u32 observed_startup_draw_clock_state(u32 field){
    return field==0?startup_draw_delivered:field==1?startup_draw_failed:startup_draw_frame;
}
''' + before)
            before = '    bool draw_startup_loading()override{\n'
            assert s.count(before) == 1
            s = s.replace(before, before + '''
        if(startup_draw_target==startup_draw_frame&&!startup_draw_delivered){
            if(startup_draw_clock<probe_clock_ns){startup_draw_failed=true;return false;}
            probe_clock_ns=startup_draw_clock;++startup_draw_delivered;
        }
''')
            before = '    bool tick(u64 now){'
            assert s.count(before) == 1
            s = s.replace(before, before + '\n        ++startup_draw_frame;\n')
            raw = s.encode()
        (fixture / name).write_bytes(raw)
    compiler = ROOT / 'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
    assert SHA(compiler.read_bytes()) == core['compilerSha256']
    flags = ['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-g0','-ffp-contract=off','-fno-strict-aliasing','-fno-exceptions','-fno-rtti',
             *['-I'+str(headers/'th12_web/cpp'/part) for part in ['game','sdl']]]
    link = ['-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576']
    run = subprocess.run([str(compiler),*flags,*link,str(fixture/'th14-vm-return-worker-fixture.cpp'),*[row['path'] for row in core['objectBindings']],'-o',str(out/'observer.wasm')],capture_output=True,env={**os.environ,'TEMP':str(out),'TMP':str(out)})
    (out/'build.log').write_bytes(run.stdout+run.stderr)
    assert run.returncode == 0, run.stderr.decode(errors='replace')[-3000:]
    report = {**core,'wasmSha256':SHA((out/'observer.wasm').read_bytes()),'engineSourcesRecompiledForThisLink':0,'engineObjectsReusedForThisLink':141,
              'fixtureBaseHashes':bindings,'fixtureGeneratedHashes':{x.name:SHA(x.read_bytes()) for x in fixture.iterdir()},
              'testOnlyStartupDrawClockInput':True,'proposedSignatureDrawClock':True,'nativeRngCounterInputOrPointerValuesProvided':False,
              'vmCallbackPointersWrapped':False,'productionNormalAnmBoundaryPoll':True,'productionNormalVmReturnPoll':True,
              'buildToolSha256':SHA(Path(__file__).read_bytes()),'reuseBuildSha256':SHA(core_raw),'completeGame':False,'nativeEquivalent':False}
    (out/'observer-build.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'compiled':True,'engineObjectsReused':141,'wasmSha256':report['wasmSha256']}))


if __name__ == '__main__':
    main()
