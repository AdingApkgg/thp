"""Build isolated TH14 GPU candidates for the collaborator's latest renderer patch."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/helper-clear-oracle-nov13'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda p: json.loads(p.read_bytes())
parent = load(R / 'artifacts/th14/upstream-helper-integration-nov12/current-provider-bindings.json')
compiler = R / 'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
assert sha(compiler) == parent['compilerSha256']
stub = R / 'artifacts/th14/boot-main-intake-nov07/application-component/include'
portable = R / 'runtimes/th12/portable/sdl'
fixture_source = R / 'tools/th14-helper-clear-oracle-nov13.cpp'
alpha_source = R / 'runtimes/th12/th12_web/tests/cpp/th14-gpu-alpha-fixture.cpp'
base_source = R / 'runtimes/th12/th12_web/tests/cpp/th14-gpu-raster-fixture.cpp'
reports = {}
attempt = sys.argv[1] if len(sys.argv) > 1 else 'v2'
assert attempt in ['v2', 'v3', 'v4']
for variant in ['baseline', 'candidate']:
    out = H / (attempt + '-' + variant)
    out.mkdir(exist_ok=False)
    sources = out / 'source'
    sources.mkdir()
    bindings = {}
    for p in [*portable.glob('*.hpp'), portable / 'Renderer.cpp']:
        actual = H / 'source-v2/runtimes/th12/portable/sdl' / p.name
        if variant == 'baseline' or not actual.is_file():
            actual = p
        (sources / p.name).write_bytes(actual.read_bytes())
        bindings[actual.relative_to(R).as_posix()] = sha(actual)
    if variant == 'candidate':
        assert 'resolve_color_clear' in (sources / 'Renderer.cpp').read_text()
        assert 'alphaRange' in (sources / 'Renderer.cpp').read_text()
    if attempt == 'v4':
        renderer = sources / 'Renderer.cpp'
        text = renderer.read_text()
        anchor = ' }\n constexpr GLenum compare[]{GL_NEVER'
        assert text.count(anchor) == 1
        text = text.replace(anchor, ' }\n#if defined(PORT_TITLE) && PORT_TITLE == 14\n else {glActiveTexture(GL_TEXTURE0);bind_texture(0);}\n#endif\n constexpr GLenum compare[]{GL_NEVER')
        renderer.write_text(text)
    base = base_source.read_text().replace('#include "../../../portable/sdl/Renderer.hpp"', '#include "Renderer.hpp"')
    base = base.replace('u32 texture_pixels[16]{};', 'u32 texture_pixels[16]{};\nu8 second_pixels[4096]{};')
    base = base.replace('    return {};', '    if(id==3)return {3,32,32,PixelFormat::Depth16,64,nullptr,0,0};\n    if(id==4)return {4,32,32,PixelFormat::Bgra8,128,second_pixels,sizeof(second_pixels),0};\n    return {};')
    (sources / 'raster-fixture.cpp').write_text(base)
    alpha = alpha_source.read_text().replace('#include "th14-gpu-raster-fixture.cpp"', '#include "raster-fixture.cpp"').replace('#include "../../../portable/sdl/Shaders.hpp"', '#include "Shaders.hpp"')
    (sources / 'alpha-fixture.cpp').write_text(alpha)
    (sources / 'fixture.cpp').write_bytes(fixture_source.read_bytes())
    for p in [fixture_source, alpha_source, base_source]:
        bindings[p.relative_to(R).as_posix()] = sha(p)
    flags = ['--target=wasm32-wasip1-threads', '-pthread', '-std=c++17', '-O2', '-g0', '-ffp-contract=off',
             '-fno-strict-aliasing', '-fno-exceptions', '-fno-rtti', '-DPORT_TITLE=14', '-D__EMSCRIPTEN__=1', '-I' + str(stub), '-I' + str(sources)]
    exports = ['gpu_initialize', 'gpu_error', 'gpu_alpha_case', 'gpu_alpha_texture', 'gpu_alpha_boundaries', 'clear_case', 'gpu_close', 'allocated', 'released']
    command = [str(compiler), *flags, '-mexec-model=reactor', '-Wl,--no-entry', '-Wl,--import-memory', '-Wl,--export-memory',
               '-Wl,--allow-undefined', '-Wl,--initial-memory=67108864', '-Wl,--max-memory=1073741824', '-Wl,-z,stack-size=1048576',
               *['-Wl,--export=' + name for name in exports], str(sources / 'Renderer.cpp'), str(sources / 'fixture.cpp'), '-o', str(out / 'probe.wasm')]
    with (out / 'build.log').open('wb') as stream:
        result = subprocess.run(command, cwd=R, stdout=stream, stderr=subprocess.STDOUT, timeout=180,
                                env={**os.environ, 'TEMP': str(out), 'TMP': str(out), 'TMPDIR': str(out)})
    if result.returncode:
        raise RuntimeError((out / 'build.log').read_text()[-5000:])
    for name, digest in bindings.items():
        assert sha(R / name) == digest, name
    report = {'variant': variant, 'sourceBindings': bindings,
              'generatedSourceBindings': {p.relative_to(R).as_posix(): sha(p) for p in sources.iterdir()},
              'compilerSha256': sha(compiler), 'flags': flags, 'wasmSha256': sha(out / 'probe.wasm'),
              'explicitTh14Branch': True, 'fixtureNormalAccess': True, 'normalRendererAccess': True, 'completeGame': False}
    report['unbindTextureForUntexturedDrawCandidate'] = attempt == 'v4'
    (out / 'build.json').write_text(json.dumps(report, indent=2) + '\n')
    reports[variant] = report['wasmSha256']
    print(json.dumps({'variant': variant, 'wasmSha256': report['wasmSha256']}), flush=True)
assert reports['baseline'] != reports['candidate'], 'The patch must change the built module'
(H / ('builds-' + attempt + '.json')).write_text(json.dumps(reports, indent=2) + '\n')
