"""Replay a retained TH14 graphics component with its unmodified C++ renderer.

Uses Wasmtime and explicitly selected standalone Windows ANGLE DLLs. No browser,
DOM, application input, real SDL window or audio device is involved. A retained
browser report can be checked as historical data, never as a current UI test.
Returns 1 when any full reference pixel buffer differs.
"""
import argparse
import collections
import ctypes as C
import hashlib
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda data: hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['build', 'reference', 'angle-directory', 'wasmtime-site', 'output']:
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--browser-baseline', type=Path)
    args = parser.parse_args()
    build_home, reference_home, out = args.build.resolve(), args.reference.resolve(), args.output.resolve()
    assert out.is_relative_to(ROOT / 'artifacts/th14') and not out.exists()
    out.mkdir(parents=True)
    storage_spec = importlib.util.spec_from_file_location('test_storage', ROOT / 'tools/th14-test-storage.py')
    storage = importlib.util.module_from_spec(storage_spec)
    storage_spec.loader.exec_module(storage)
    storage.check_budget(out, 100 * 1024**3, 2 * 1024**3)
    sys.path.insert(0, str(args.wasmtime_site.resolve()))
    import wasmtime as W
    context_path = ROOT / 'tools/th14-native-gles-context.py'
    spec = importlib.util.spec_from_file_location('native_gles_context', context_path)
    graphics = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(graphics)
    build_bytes = (build_home / 'build.json').read_bytes()
    build = json.loads(build_bytes)
    for path, binding in build['sourceBindings'].items():
        raw = (ROOT / path).read_bytes()
        assert len(raw) == binding['bytes'] and SHA(raw) == binding['sha256'], path
    for name, digest in build['sourceFiles'].items():
        assert SHA((build_home / 'src' / name).read_bytes()) == digest, name
    for name, digest in build['shimFiles'].items():
        assert SHA((build_home / 'include' / name).read_bytes()) == digest, name
    wasm = (build_home / 'probe.wasm').read_bytes()
    assert SHA(wasm) == build['wasmSha256']
    signatures_bytes = (build_home / 'gl-signatures.json').read_bytes()
    assert SHA(signatures_bytes) == build['signaturesSha256']
    signatures = json.loads(signatures_bytes)
    engine, store = W.Engine(), None
    module = W.Module(engine, wasm)
    store = W.Store(engine)
    wasi = W.WasiConfig()
    wasi.stdout_file, wasi.stderr_file = str(out / 'stdout.log'), str(out / 'stderr.log')
    store.set_wasi(wasi)
    linker = W.Linker(engine)
    linker.define_wasi()
    calls, shader_sources = collections.Counter(), []
    context = graphics.Context(args.angle_directory)

    def ctype(value):
        value = value.replace('const', '').strip()
        if '*' in value:
            return C.c_void_p
        return {'void': None, 'GLenum': C.c_uint, 'GLbitfield': C.c_uint, 'GLuint': C.c_uint, 'GLint': C.c_int, 'GLsizei': C.c_int, 'GLboolean': C.c_ubyte, 'GLfloat': C.c_float, 'GLclampf': C.c_float, 'GLintptr': C.c_ssize_t, 'GLsizeiptr': C.c_ssize_t}[value]

    def host(name):
        signature = signatures[name]
        function = graphics.fn(context.gles, name, ctype(signature['result']), *[ctype(value) for value in signature['args']])

        def invoke(caller, *arguments):
            calls[name] += 1
            memory = caller['memory']
            address = C.addressof(memory.data_ptr(caller).contents)
            if name == 'glShaderSource':
                shader, count, strings, lengths = arguments
                array, owned = (C.c_char_p * count)(), []
                for index in range(count):
                    pointer = struct.unpack('<I', memory.read(caller, strings + index * 4, strings + index * 4 + 4))[0]
                    length = struct.unpack('<i', memory.read(caller, lengths + index * 4, lengths + index * 4 + 4))[0] if lengths else -1
                    raw = C.string_at(address + pointer, length) if length >= 0 else C.string_at(address + pointer)
                    owned.append(raw)
                    array[index] = raw
                shader_sources.append(b''.join(owned).decode())
                function(shader, count, array, C.c_void_p(address + lengths) if lengths else None)
                return
            values = []
            for index, (value, kind) in enumerate(zip(arguments, signature['args'])):
                if '*' in kind:
                    buffer_offset = (name in ['glVertexAttribPointer', 'glVertexAttribIPointer'] and index == len(arguments) - 1) or (name.startswith('glDrawElements') and index == 3)
                    values.append(C.c_void_p(value if buffer_offset else address + value if value else 0))
                else:
                    values.append(value)
            return function(*values)
        return invoke

    try:
        for imported in module.imports:
            if imported.module == 'wasi_snapshot_preview1':
                continue
            assert imported.module == 'env', imported.module
            if imported.name == 'touhou_clip_control':
                callback = lambda caller: context.clip_control()
            else:
                assert imported.name in signatures, imported.name
                callback = host(imported.name)
            linker.define(store, imported.module, imported.name, W.Func(store, imported.type, callback, access_caller=True))
        instance = linker.instantiate(store, module)
        api = instance.exports(store)
        api['_initialize'](store)
        memory = api['memory']
        call = lambda name, *arguments: api[name](store, *arguments)
        assert call('gpu_initialize') == 1, C.string_at(C.addressof(memory.data_ptr(store).contents) + call('gpu_error')).decode()
        gl_error = graphics.fn(context.gles, 'glGetError', C.c_uint)
        assert gl_error() == 0
        prepared_bytes = (reference_home / 'prepared.json').read_bytes()
        prepared = json.loads(prepared_bytes)
        native_bytes = (reference_home / 'native.json').read_bytes()
        native = json.loads(native_bytes)
        reference = (reference_home / 'native.bgra').read_bytes()
        assert SHA(reference) == native['pixelsSha256']
        assert 0 < len(prepared['frames']) <= 64

        def upload(data):
            pointer = call('gpu_allocate', len(data))
            assert pointer
            memory.write(store, data, pointer)
            return pointer

        texture_bindings = []
        for texture in prepared['textures']:
            path = (reference_home / texture['file']).resolve()
            assert path.is_relative_to(reference_home)
            data = path.read_bytes()
            assert SHA(data) == texture['sha256']
            pointer = upload(data)
            assert call('gpu_texture', texture['handle'], texture['width'], texture['height'], texture['format'], texture['pitch'], pointer, len(data)) == 1
            texture_bindings.append(dict(handle=texture['handle'], bytes=len(data), sha256=SHA(data)))

        def words(data, function):
            raw = struct.pack('<' + 'I' * len(data), *(value & 0xffffffff for value in data))
            pointer = upload(raw or bytes(4))
            try:
                return function(pointer)
            finally:
                call('gpu_release', pointer)

        def execute(command):
            kind = command['kind']
            if kind == 'renderState':
                ok = call('gpu_render_state', command['key'], command['value'])
            elif kind == 'samplerState':
                ok = call('gpu_sampler', command['sampler'], command['key'], command['value'])
            elif kind == 'textureStageState':
                ok = call('gpu_texture_stage', command['stage'], command['key'], command['value'])
            elif kind == 'texture':
                ok = call('gpu_bind', command['sampler'], command['handle'])
            elif kind == 'fvf':
                ok = call('gpu_fvf', command['value'])
            elif kind == 'transform':
                ok = words(command['words'], lambda pointer: call('gpu_matrix', command['key'], pointer))
            elif kind == 'viewport':
                ok = words(command['words'], lambda pointer: call('gpu_viewport', pointer))
            elif kind == 'clear':
                ok = words(command['rectangles'], lambda pointer: call('gpu_clear', command['flags'], command['color'], command['depthWord'], command['stencil'], pointer, len(command['rectangles']) // 4))
            elif kind == 'draw':
                ok = words(command['words'], lambda pointer: call('gpu_draw', command['topology'], command['count'], command['stride'], pointer))
            elif kind in ['controlledScreenQueue', 'controlledScreenFlush']:
                ok = 1  # Same explicit exclusion as the original retained fixture.
            else:
                raise AssertionError(kind)
            assert ok, command

        rows, actual_hash = [], hashlib.sha256()
        for frame in prepared['frames']:
            storage.check_budget(out, 100 * 1024**3, 2 * 1024**3)
            target = next(row for row in native['frames'] if (row['stage'], row['frame']) == (frame['stage'], frame['frame']))
            assert target['bytes'] == 640 * 480 * 4 and call('gpu_begin') == 1
            for command in frame['initialState'] + frame['commands']:
                execute(command)
            pointer = call('gpu_read')
            assert pointer
            raw = bytes(memory.read(store, pointer, pointer + target['bytes']))
            expected = reference[target['offset']:target['offset'] + target['bytes']]
            assert len(raw) == len(expected) == target['bytes'] and SHA(expected) == target['sha256']
            differences = [(index, left, right) for index, (left, right) in enumerate(zip(raw, expected)) if left != right]
            assert gl_error() == 0
            actual_hash.update(raw)
            (out / f"stage{frame['stage']}-frame{frame['frame']}.bgra").write_bytes(raw)
            row = dict(stage=frame['stage'], frame=frame['frame'], differentChannels=len(differences), actualSha256=SHA(raw), originalSha256=SHA(expected), first=[dict(x=index // 4 % 640, y=index // 2560, channel=index % 4, actual=left, original=right) for index, left, right in differences[:12]])
            rows.append(row)
            print(json.dumps(row), flush=True)
        result = dict(frames=len(rows), exactFrames=sum(not row['differentChannels'] for row in rows), differentChannels=sum(row['differentChannels'] for row in rows), strictPixelsEqual=all(not row['differentChannels'] for row in rows), rows=rows, contextInfo=context.info, clipControlEnabled=True, glCalls=dict(calls), shaderHashes=[SHA(source.encode()) for source in shader_sources], textureBindings=texture_bindings, wasmSha256=SHA(wasm), nativePixelsSha256=SHA(reference), actualPixelsSha256=actual_hash.hexdigest(), preparedSha256=SHA(prepared_bytes), nativeReportSha256=SHA(native_bytes), buildSha256=SHA(build_bytes), toolSha256=SHA(Path(__file__).read_bytes()), contextToolSha256=SHA(context_path.read_bytes()), wasmtimeVersion=importlib.metadata.version('wasmtime'), originalRendererSourcesUnmodified=True, browserRun=False, browserAcceptance=False, appUiControlled=False, audioDevicesOpened=0, productionChanged=False, completeGame=False, nativeEquivalent=False, scope='Finite retained Stage command streams only. Same production C++ renderer and shaders with a deterministic SDL lifetime shim and standalone ANGLE D3D11. Explicit controlled screen-queue exclusions retained. No whole scene, actual original framebuffer, native cold-menu, current browser or complete-game claim.')
        if args.browser_baseline:
            baseline_bytes = args.browser_baseline.read_bytes()
            baseline = json.loads(baseline_bytes)
            for path, binding in baseline['sourceBindings'].items():
                assert build['sourceBindings'][path] == binding
            assert baseline['gpu']['clipControlAvailable'] and baseline['gpu']['clipDepthMode'] == baseline['gpu']['clipZeroToOne']
            sources = {shader['actualApiSourceSha256'] for context_row in baseline['shaderBackend']['contexts'] for program in context_row['programs'] for shader in program['shaders']}
            frames_equal = len(baseline['reports']) == len(rows) and all(row['actualSha256'] == previous['portableSha256'] for row, previous in zip(rows, baseline['reports']))
            source_equal = sources == set(result['shaderHashes'])
            result['retainedBrowserBaseline'] = dict(reportSha256=SHA(baseline_bytes), allFullBuffersReproduced=frames_equal, allShaderSourcesIdentical=source_equal, distinctShaderSources=len(sources), currentBrowserAcceptance=False)
            assert frames_equal and source_equal, 'Standalone component does not reproduce the retained browser component'
        (out / 'shader-sources.json').write_text(json.dumps(shader_sources, indent=2) + '\n')
        (out / 'comparison.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps({key: result[key] for key in ['frames', 'exactFrames', 'differentChannels', 'strictPixelsEqual']}))
        return 0 if result['strictPixelsEqual'] else 1
    finally:
        context.close()


if __name__ == '__main__':
    sys.exit(main())
