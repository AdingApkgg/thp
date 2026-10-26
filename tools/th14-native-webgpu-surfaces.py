"""Compare actual C++ WebGPU resampling to retained original D3DX buffers."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda raw: hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['build', 'reference', 'wgpu-site', 'wasmtime-site', 'output']:
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    out, home, build_home = args.output.resolve(), args.reference.resolve(strict=True), args.build.resolve(strict=True)
    assert out.is_relative_to(ROOT/'artifacts/th14') and not out.exists()
    out.mkdir(parents=True)
    spec = importlib.util.spec_from_file_location('storage', ROOT/'tools/th14-test-storage.py')
    storage = importlib.util.module_from_spec(spec); spec.loader.exec_module(storage); storage.check_budget(out)
    build_raw = (build_home/'build.json').read_bytes(); build = json.loads(build_raw)
    assert build['backend'] == 'webgpu'
    for path, binding in build['sourceBindings'].items():
        assert SHA((ROOT/path).read_bytes()) == binding['sha256'], path
    for name, digest in build['sourceFiles'].items():
        assert SHA((build_home/'src'/name).read_bytes()) == digest, name
    wasm = (build_home/'probe.wasm').read_bytes(); assert SHA(wasm) == build['wasmSha256']
    reference_raw = (home/'native.json').read_bytes(); native = json.loads(reference_raw)
    inputs_raw = (home/'inputs.json').read_bytes(); inputs = json.loads(inputs_raw)
    source = (home/'source.bgra').read_bytes(); assert SHA(source) == inputs['sourceSha256']
    assert native['sourceUploadReadbackByteExact'] and len(native['cases']) == 8
    sys.path.insert(0, str(args.wasmtime_site.resolve(strict=True)))
    import wasmtime as W
    host_path = ROOT/'tools/th14-native-webgpu-context.py'
    spec = importlib.util.spec_from_file_location('gpu_host', host_path)
    host = importlib.util.module_from_spec(spec); spec.loader.exec_module(host)
    context = host.Context(args.wgpu_site, build_home/'src/Th14WebGpu.wgsl')
    engine = W.Engine(); store = W.Store(engine); wasi = W.WasiConfig()
    wasi.stdout_file = str(out/'stdout.log'); wasi.stderr_file = str(out/'stderr.log'); store.set_wasi(wasi)
    module = W.Module(engine, wasm); linker = W.Linker(engine); linker.define_wasi()
    def callback(name):
        def invoke(caller, *values):
            assert name.startswith('th14_webgpu_'), 'Unexpected GLES call: '+name
            return context.invoke(name, caller, *values)
        return invoke
    try:
        for item in module.imports:
            if item.module != 'wasi_snapshot_preview1':
                assert item.module == 'env'
                linker.define(store, item.module, item.name, W.Func(store, item.type, callback(item.name), access_caller=True))
        instance = linker.instantiate(store, module); api = instance.exports(store); api['_initialize'](store)
        call = lambda name, *values: api[name](store, *values)
        memory = api['memory']; owned = []
        def upload(raw):
            pointer = call('gpu_allocate', len(raw)); assert pointer
            memory.write(store, raw, pointer); owned.append(pointer); return pointer
        def words(values): return upload(struct.pack('<'+'i'*len(values), *values))
        def surface(handle, width, height, fmt, raw, bpp):
            assert call('gpu_surface', handle, width, height, fmt, width*bpp, upload(raw), len(raw)) == 1
        def read(handle, size):
            ptr = call('gpu_read', handle); return bytes(memory.read(store, ptr, ptr+size))
        assert call('gpu_initialize') == 1
        surface(1, 640, 480, 1, source, 4)
        rows = []
        for case in native['cases']:
            bpp = case['bpp']; assert (case['destinationFormat'], bpp) in [(23, 2), (21, 4)]
            value = inputs['targetRgb565Prefill'] if bpp == 2 else inputs['targetArgb8Prefill']
            surface(2, 512, 512, 3 if bpp == 2 else 1, value.to_bytes(bpp, 'little')*(512*512), bpp)
            assert call('gpu_resample', 1, words(case['sourceRect']), 2, words(case['destinationRect']), 0, 0, 0) == 1
            actual = read(2, case['bytes']); expected = (home/case['pixelFile']).read_bytes()
            assert SHA(expected) == case['pixelSha256'] and len(actual) == len(expected)
            different = sum(a != b for a, b in zip(actual, expected))
            (out/f"case-{case['index']}.pixels").write_bytes(actual)
            row = dict(index=case['index'], name=case['name'], bytes=len(actual), differentBytes=different,
                actualSha256=SHA(actual), nativeSha256=SHA(expected))
            rows.append(row); print(json.dumps(row), flush=True)
        # Small independent rectangle controls exercise actual writes, partial
        # clears, CPU version invalidation, GPU-to-GPU copy and readback.
        width, height = 96, 128; prefill = bytes.fromhex('a1b2c3d4')*(width*height)
        surface(3, width, height, 1, prefill, 4)
        boxes = [(3, 7, 49, 61), (47, 43, 90, 119)]; color = 0xffa15127
        call('gpu_clear', 3, color, words([v for rect in boxes for v in rect]), len(boxes))
        expected = bytearray(prefill)
        for left, top, right, bottom in boxes:
            for y in range(top, bottom):
                expected[(y*width+left)*4:(y*width+right)*4] = color.to_bytes(4, 'little')*(right-left)
        cleared = read(3, len(expected)); assert cleared == expected
        (out/'partial-clear.bgra').write_bytes(cleared)
        ptr = call('gpu_read', 3); replacement = bytes.fromhex('225577ff')
        memory.write(store, replacement, ptr+(8*width+4)*4); expected[(8*width+4)*4:(8*width+5)*4] = replacement
        call('gpu_dirty', 3)
        surface(4, width, height, 1, prefill, 4)
        call('gpu_copy', 3, words([4, 8, 39, 51]), 4, words([17, 19]))
        copied = bytearray(prefill)
        for y in range(43):
            copied[((19+y)*width+17)*4:((19+y)*width+52)*4] = expected[((8+y)*width+4)*4:((8+y)*width+39)*4]
        copied_actual = read(4, len(copied)); assert copied_actual == copied
        (out/'version-copy.bgra').write_bytes(copied_actual)
        call('gpu_present', 4)
        result = dict(schema='th14/cpp-webgpu-surfaces/1', cases=len(rows), exactCases=sum(not r['differentBytes'] for r in rows),
            differentBytes=sum(r['differentBytes'] for r in rows), comparedBytes=sum(r['bytes'] for r in rows), rows=rows,
            rectangleControls=dict(partialClearRectangles=2, cpuVersionInvalidation=True, copiedRectangleBytes=35*43*4, exact=True),
            buildSha256=SHA(build_raw), wasmSha256=SHA(wasm), nativeReportSha256=SHA(reference_raw), inputsSha256=SHA(inputs_raw),
            sourceSha256=SHA(source), hostToolSha256=SHA(host_path.read_bytes()), toolSha256=SHA(Path(__file__).read_bytes()),
            renderer=context.info, gpuCalls=dict(context.calls), actualProductionCppRenderer=True, browserAcceptance=False,
            completeGame=False, nativeEquivalent=False, scope='Eight retained original32 D3DX HAL POINT/format/rectangle buffers versus actual C++ Renderer WebGPU resample. Synthetic input pixels and original declared prefill; original output never enters rendering. Additional partial-clear/CPU-version/copy controls have independent byte-array expectations. No full game or browser proof.')
        (out/'report.json').write_text(json.dumps(result, indent=2)+'\n')
        return int(result['exactCases'] != result['cases'])
    finally:
        context.close()


if __name__ == '__main__':
    sys.exit(main())
