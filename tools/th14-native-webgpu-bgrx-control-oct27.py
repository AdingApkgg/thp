"""Actual WASI C++ Renderer and native GPU host versus D3D9/D3DX A8/X8 buffers."""
from pathlib import Path
import argparse
import collections
import hashlib
import importlib.util
import json
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in['build','reference','wasmtime-site','wgpu-site','output']:parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();out=args.output.resolve();build_home=args.build.resolve();reference=args.reference.resolve()
    assert out.is_relative_to(ROOT/'artifacts/th14')and not out.exists();out.mkdir()
    tool=Path(__file__).read_bytes();(out/'run-tool.py').write_bytes(tool)
    context_path=ROOT/'tools/th14-native-webgpu-context.py';context_tool=context_path.read_bytes();(out/'context-tool.py').write_bytes(context_tool)
    spec=importlib.util.spec_from_file_location('graphics',context_path);graphics=importlib.util.module_from_spec(spec);spec.loader.exec_module(graphics)
    build_raw=(build_home/'build.json').read_bytes();build=json.loads(build_raw);wasm=(build_home/'probe.wasm').read_bytes()
    assert build['backend']=='webgpu'and SHA(wasm)==build['wasmSha256']
    for path,row in build['sourceBindings'].items():assert SHA((ROOT/path).read_bytes())==row['sha256'],path
    for name,digest in build['sourceFiles'].items():assert SHA((build_home/'src'/name).read_bytes())==digest,name
    for name,digest in build['shimFiles'].items():assert SHA((build_home/'include'/name).read_bytes())==digest,name
    native_raw=(reference/'report.json').read_bytes();native=json.loads(native_raw)
    assert native['caseCount']==1344 and native['actualD3d9Hal']and native['actualD3dxFormatConversion']
    sys.path.insert(0,str(args.wasmtime_site.resolve()));import wasmtime as W
    engine=W.Engine();store=W.Store(engine);wasi=W.WasiConfig();wasi.stdout_file=str(out/'stdout.log');wasi.stderr_file=str(out/'stderr.log');store.set_wasi(wasi)
    signatures_raw=(build_home/'gl-signatures.json').read_bytes();assert SHA(signatures_raw)==build['signaturesSha256'];signatures=json.loads(signatures_raw)
    module=W.Module(engine,wasm);linker=W.Linker(engine);linker.define_wasi();context=graphics.Context(args.wgpu_site,build_home/'src/Th14WebGpu.wgsl');calls=collections.Counter();rows=[];closed=False;gles_imports=[]
    try:
        for imported in module.imports:
            if imported.module=='wasi_snapshot_preview1':continue
            assert imported.module=='env'
            if imported.name.startswith('th14_webgpu_'):
                def callback(caller,*values,name=imported.name):calls[name]+=1;return context.invoke(name,caller,*values)
            else:
                assert imported.name.startswith('gl')and imported.name in signatures,imported.name
                gles_imports.append(imported.name)
                def callback(caller,*values,name=imported.name):
                    calls[name]+=1;raise RuntimeError('Unexecuted GLES fallback import was called: '+name)
            linker.define(store,imported.module,imported.name,W.Func(store,imported.type,callback,access_caller=True))
        api=linker.instantiate(store,module).exports(store);api['_initialize'](store);memory=api['memory'];call=lambda name,*values:api[name](store,*values)
        assert call('gpu_initialize')==1
        def clear(color,rects):
            if rects:
                raw=struct.pack('<'+'i'*len(rects)*4,*(v for box in rects for v in box));pointer=call('gpu_allocate',len(raw));memory.write(store,raw,pointer)
            else:pointer=0
            try:assert call('gpu_clear',color,pointer,len(rects)if rects else 0)==1
            finally:
                if pointer:call('gpu_release',pointer)
        def pixels():
            pointer=call('gpu_read');assert pointer;return bytes(memory.read(store,pointer,pointer+1024))
        for row in native['cases']:
            assert call('gpu_case',row['format'])==1
            assert call('gpu_blend',0,2,1,1,row['colorMask'])==1
            clear(row['clearColor'],None);clear(row['partialColor'],row['rectangles']);buffers=dict(clear=pixels())
            assert call('gpu_blend',int(row['blendEnabled']),row['sourceBlend'],row['destinationBlend'],row['blendOperation'],row['colorMask'])==1
            assert call('gpu_draw',row['sourceColor'],0.,0.,16.,16.)==1;buffers['first']=pixels()
            assert call('gpu_blend',1,7,8,1,15)==1;assert call('gpu_draw',0x6b27a1d3,4.,5.,14.,15.)==1;buffers['chain']=pixels();comparisons=[]
            for label,raw in buffers.items():
                expected=(reference/row['buffers'][label]['file']).read_bytes();assert SHA(expected)==row['buffers'][label]['sha256']
                assert len(raw)==len(expected)==1024
                file=f"case-{row['index']:04d}-{label}.bgra";(out/file).write_bytes(raw)
                comparisons.append(dict(label=label,file=file,bytes=len(raw),differentBytes=sum(a!=b for a,b in zip(raw,expected)),sha256=SHA(raw),halSha256=SHA(expected)))
            rows.append(dict(index=row['index'],format=row['format'],comparisons=comparisons))
            if len(rows)%224==0:print(json.dumps(dict(cases=len(rows),differentBytes=sum(c['differentBytes']for r in rows for c in r['comparisons']))),flush=True)
        call('gpu_close');closed=True
        assert not any(calls[name]for name in gles_imports)
        result=dict(schema='th14/native-cpp-webgpu-bgrx-raster/1',caseCount=len(rows),rows=rows,comparedBuffers=len(rows)*3,comparedBytes=len(rows)*3*1024,
            differentBytes=sum(c['differentBytes']for r in rows for c in r['comparisons']),actualCppRenderer=True,actualNativeGpu=True,
            wasmSha256=SHA(wasm),buildSha256=SHA(build_raw),nativeReportSha256=SHA(native_raw),contextSha256=SHA(context_tool),toolSha256=SHA(tool),gpuCalls=dict(calls),
            sourceFrozenAtStart=True,unexecutedGlesImportsBoundToRejectingTraps=gles_imports,glesFallbackCalls=0,
            actualEmscriptenAsyncify=False,browserRun=False,browserAcceptance=False,physicalAudioDevicesOpened=0,completeGame=False,nativeEquivalent=False,
            scope='Actual WASI C++ Renderer and real native GPU host with1344 A8/X8 Clear/draw/read cases versus actual D3D9/D3DX canonical outputs. No browser, physical UI/audio, original full-game or all-format equivalence.')
        assert context_path.read_bytes()==context_tool
        (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({key:result[key]for key in['caseCount','comparedBuffers','comparedBytes','differentBytes']}))
        assert result['caseCount']==1344 and not result['differentBytes']
    finally:
        if not closed:context.close()


if __name__=='__main__':main()
