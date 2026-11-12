"""Build normal-access loading probes with explicit template-owner lifetimes."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode', choices=['live-preparer', 'scoped-owner'], required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    out = a.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    sha = lambda f: hashlib.sha256(f.read_bytes()).hexdigest()
    home = ROOT / 'artifacts/th14/loading-control4-nov13'
    base = json.loads((home / 'component/build.json').read_bytes())
    provider_path = Path(base['providerBuild'])
    provider = json.loads(provider_path.read_bytes())
    assert provider['normalEngineAccessControl']
    for name, digest in {**base['sourceBindings'], **base['observerBindings']}.items():
        assert sha(ROOT / name) == digest, name
    for row in provider['currentProviders']:
        assert sha(ROOT / row['object']) == row['objectSha256']
    source = (home / 'rate-diagnostic-v2/fixture.cpp').read_text()
    if a.mode == 'live-preparer':
        old = 'std::unique_ptr<AnmManager> owner;'
        assert source.count(old) == 1
        source = source.replace(old, old + '\nstd::unique_ptr<AnmManager> template_owner;')
        old = 'API(setup) u32 setup(const u8* bytes,u32 size){return ascii.open(bytes,size);}'
        new = '''API(setup) u32 setup(const u8* bytes,u32 size){
 if(!ascii.open(bytes,size))return 0;
 template_owner=std::make_unique<AnmManager>();
 template_owner->rate=1;template_owner->fallback_sprites=&ascii;
 return template_owner->prepare_resource(ascii,2);
}'''
        assert source.count(old) == 1
        source = source.replace(old, new)
    else:
        old = ' a.rate=rate;a.fallback_sprites=&ascii;'
        assert source.count(old) == 1
        source = source.replace(old, ' a.rate=1;a.fallback_sprites=&ascii;')
        old = ' if(!a.prepare_resource(ascii,2))return 0;'
        assert source.count(old) == 1
        source = source.replace(old, old + '\n a.rate=rate;')
        old = 'owner.reset();seen.clear();}'
        assert source.count(old) == 1
        source = source.replace(old, 'ascii.templates.reset();owner.reset();seen.clear();}')
    fixture = out / 'fixture.cpp'
    fixture.write_text(source, encoding='utf8', newline='\n')
    cc = ROOT / 'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
    assert sha(cc) == provider['compilerSha256']
    command = [str(cc), *provider['flags'], '-mexec-model=reactor', '-Wl,--no-entry',
               '-Wl,--import-memory', '-Wl,--export-memory', '-Wl,--allow-undefined',
               '-Wl,--initial-memory=67108864', '-Wl,--max-memory=1073741824',
               '-Wl,-z,stack-size=1048576', str(fixture),
               *[row['object'] for row in provider['currentProviders']], '-o', str(out / 'probe.wasm')]
    env = dict(os.environ, TEMP=str(out), TMP=str(out), TMPDIR=str(out))
    with (out / 'build.log').open('wb') as stream:
        subprocess.run(command, cwd=ROOT, env=env, stdout=stream,
                       stderr=subprocess.STDOUT, check=True, timeout=120)
    bindings = dict(base['observerBindings'])
    for path in [Path(__file__), fixture, home / 'rate-diagnostic-v2/fixture.cpp']:
        bindings[path.relative_to(ROOT).as_posix()] = sha(path)
    report = dict(base, observerBindings=bindings, command=command,
                  wasmSha256=sha(out / 'probe.wasm'), lifetimeMode=a.mode,
                  templatePreparationRate=1, engineUnitsChanged=0,
                  dereferenceObservedPointers=False, completeGame=False)
    (out / 'build.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'mode': a.mode, 'wasmSha256': report['wasmSha256']}))


if __name__ == '__main__':
    main()
