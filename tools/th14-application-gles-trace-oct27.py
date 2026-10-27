"""Replay observed semantic batches through the actual C++ GLES Renderer.

The fixture exposes issue() for diagnostics without changing Renderer.cpp or
shader arithmetic. A complete baseline match is required before comparing
retained independent D3D9 hashes. No browser or original process is controlled.
"""
from pathlib import Path
import argparse
import collections
import ctypes as C
import hashlib
import importlib.util
import json
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['build','trace','native-comparisons','baseline','output']:
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--angle-directory',type=Path,default=Path('C:/Users/APKGG/AppData/Local/Programs/Trae'))
    parser.add_argument('--wasmtime-site',type=Path,default=ROOT/'tools/tmp/th14-native-gles-python/site')
    parser.add_argument('--probe-draw',type=int,nargs='*',default=[],help='Observe unblended source fragments on an independent float target')
    parser.add_argument('--uv-probe',action='store_true',help='Private shader observation with a disabled-by-default UV output uniform')
    parser.add_argument('--baseline-kind',choices=['current-application','independent-hal'],default='current-application')
    parser.add_argument('--expected-frame',type=int,default=2264,help='Explicit Application frame represented by this trace')
    args=parser.parse_args();out=args.output.resolve();build_home=args.build.resolve();source=args.trace.resolve(strict=True)
    assert out.is_relative_to(ROOT/'artifacts/th14')and not out.exists();out.mkdir(parents=True)
    storage=load('trace_storage',ROOT/'tools/th14-test-storage.py');storage.check_budget(out,100*1024**3,128*1024**2)
    (out/'runner.py').write_bytes(Path(__file__).read_bytes())
    trace_raw=source.read_bytes();trace=json.loads(trace_raw);assert 1<=args.expected_frame<=240000 and trace['frame']==args.expected_frame
    expected_draws=sum(row['kind']==101 for row in trace['events']);expected_clears=sum(row['kind']==110 for row in trace['events'])
    assert expected_draws>0 and expected_clears>0
    native_raw=args.native_comparisons.read_bytes();native=json.loads(native_raw)
    expected={row['event']:row for row in native['steps']}
    build=json.loads((build_home/'build.json').read_bytes())
    for path,row in build['sourceBindings'].items():
        raw=(ROOT/path).read_bytes();assert len(raw)==row['bytes']and SHA(raw)==row['sha256'],path
    for folder,key in [('src','sourceFiles'),('include','shimFiles')]:
        for path,digest in build[key].items():assert SHA((build_home/folder/path).read_bytes())==digest,path
    wasm=(build_home/'probe.wasm').read_bytes();assert SHA(wasm)==build['wasmSha256']
    signature_raw=(build_home/'gl-signatures.json').read_bytes();assert SHA(signature_raw)==build['signaturesSha256'];signatures=json.loads(signature_raw)
    sys.path.insert(0,str(args.wasmtime_site));import wasmtime as W
    graphics=load('trace_graphics',ROOT/'tools/th14-native-gles-context.py');context=graphics.Context(args.angle_directory)
    engine=W.Engine();module=W.Module(engine,wasm);store=W.Store(engine);wasi=W.WasiConfig()
    wasi.stdout_file=str(out/'stdout.log');wasi.stderr_file=str(out/'stderr.log');store.set_wasi(wasi)
    linker=W.Linker(engine);linker.define_wasi();calls=collections.Counter();shaders=[];active_uv=False
    def ctype(value):
        value=value.replace('const','').strip()
        if '*'in value:return C.c_void_p
        return {'void':None,'GLenum':C.c_uint,'GLbitfield':C.c_uint,'GLuint':C.c_uint,'GLint':C.c_int,'GLsizei':C.c_int,
            'GLboolean':C.c_ubyte,'GLfloat':C.c_float,'GLclampf':C.c_float,'GLintptr':C.c_ssize_t,'GLsizeiptr':C.c_ssize_t}[value]
    def host(name):
        signature=signatures[name];function=graphics.fn(context.gles,name,ctype(signature['result']),*[ctype(value)for value in signature['args']])
        def invoke(caller,*arguments):
            calls[name]+=1;memory=caller['memory'];address=C.addressof(memory.data_ptr(caller).contents)
            if name=='glShaderSource':
                shader,count,strings,lengths=arguments;array=(C.c_char_p*count)();owned=[]
                for i in range(count):
                    pointer=struct.unpack('<I',memory.read(caller,strings+i*4,strings+i*4+4))[0]
                    length=struct.unpack('<i',memory.read(caller,lengths+i*4,lengths+i*4+4))[0]if lengths else -1
                    raw=C.string_at(address+pointer,length)if length>=0 else C.string_at(address+pointer)
                    owned.append(raw);array[i]=raw
                source=b''.join(owned).decode()
                if args.uv_probe and 'in vec2 vUV;'in source:
                    assert source.count('outColor=c;')==1
                    source=source.replace('out vec4 outColor;','out vec4 outColor;uniform bool traceUvOnly;')
                    source=source.replace('outColor=c;','outColor=traceUvOnly?vec4(vUV,0.0,1.0):c;').replace('if(!pass)discard;','if(!pass&&!traceUvOnly)discard;')
                    encoded=source.encode();array=(C.c_char_p*1)(encoded);function(shader,1,array,None)
                else:function(shader,count,array,C.c_void_p(address+lengths)if lengths else None)
                shaders.append(source);return
            if args.uv_probe and name in ['glDrawArrays','glDrawArraysInstanced','glDrawElements','glDrawElementsInstanced']:
                program=C.c_int();graphics.fn(context.gles,'glGetIntegerv',None,C.c_uint,C.POINTER(C.c_int))(0x8b8d,C.byref(program))
                get_location=C.WINFUNCTYPE(C.c_int,C.c_uint,C.c_char_p)(C.cast(context.gles.glGetUniformLocation,C.c_void_p).value)
                location=get_location(program.value,b'traceUvOnly')
                if location>=0:graphics.fn(context.gles,'glUniform1i',None,C.c_int,C.c_int)(location,int(active_uv))
            values=[]
            for i,(value,kind)in enumerate(zip(arguments,signature['args'])):
                if '*'in kind:
                    offset=(name in ['glVertexAttribPointer','glVertexAttribIPointer']and i==len(arguments)-1)or(name.startswith('glDrawElements')and i==3)
                    values.append(C.c_void_p(value if offset else address+value if value else 0))
                else:values.append(value)
            return function(*values)
        return invoke
    steps=[];first_targets=set();last_colors={};draws=0;clears=0;completed=False;error='';baseline_exact=False;allocations=[]
    try:
        for imported in module.imports:
            if imported.module=='wasi_snapshot_preview1':continue
            assert imported.module=='env'
            callback=(lambda caller:context.clip_control())if imported.name=='touhou_clip_control'else host(imported.name)
            linker.define(store,'env',imported.name,W.Func(store,imported.type,callback,access_caller=True))
        api=linker.instantiate(store,module).exports(store);api['_initialize'](store);memory=api['memory']
        call=lambda name,*a:api[name](store,*a)
        assert call('gpu_initialize')==1
        gl_error=graphics.fn(context.gles,'glGetError',C.c_uint);assert gl_error()==0
        def upload(raw):
            if not raw:return 0
            pointer=call('gpu_allocate',len(raw));assert pointer;memory.write(store,raw,pointer);allocations.append(pointer);return pointer
        def words(w):return upload(struct.pack('<'+'I'*len(w),*(v&0xffffffff for v in w)))
        cache={}
        def blob(row):
            if row['sha256']not in cache:
                path=(source.parent/row['file']).resolve(strict=True);assert path.is_relative_to(source.parent)
                raw=path.read_bytes();assert len(raw)==row['bytes']and SHA(raw)==row['sha256'];cache[row['sha256']]=raw
            return cache[row['sha256']]
        initial={r['handle']:r for r in trace['initial']['resources']};metadata={}
        for row in trace['events']:
            if row['kind']==4:
                w=row['words'];old=metadata.get(w[0]);assert old is None or(old['words']==w and old.get('blob')==row.get('blob'))
                metadata[w[0]]=row
        targets={r['words'][1]for r in trace['events']if r['kind']==1};assert targets=={1,9,10}
        for handle,row in metadata.items():
            w=row['words'];raw=b''if w[3]==10 else blob(initial[handle]['pixels'])if handle in targets else blob(row['blob'])if row.get('blob')else blob(initial[handle]['pixels'])
            fmt=1 if handle in targets else w[3];pitch=w[1]*4 if handle in targets else w[4]
            assert call('gpu_surface',handle,w[1],w[2],fmt,pitch,upload(raw),len(raw),w[6])==1
            if fmt!=10:assert call('gpu_seed',handle)==1
            if handle in targets:last_colors[handle]=raw
        def read(handle):
            row=metadata[handle]['words'];pointer=call('gpu_read',handle);assert pointer
            return bytes(memory.read(store,pointer,pointer+row[1]*row[2]*4))
        def compare(event,handle,semantic=None):
            raw=read(handle);oracle=expected[event];digest=SHA(raw)
            assert oracle['target']==handle and oracle['completedDraws']==draws
            row=dict(event=event,completedDraws=draws,target=handle,glesSha256=digest,nativeSha256=oracle['nativeSha256'],nativeHashEqual=digest==oracle['nativeSha256'])
            if not row['nativeHashEqual']and handle not in first_targets:
                first_targets.add(handle);stem='first-target-'+str(handle)
                (out/(stem+'-gles.bgra')).write_bytes(raw);(out/(stem+'-before-gles.bgra')).write_bytes(last_colors[handle])
                row['previousGlesSha256']=SHA(last_colors[handle]);row['semanticStateWords']=semantic
                (out/(stem+'-state.json')).write_text(json.dumps(row,indent=2)+'\n');print(json.dumps(dict(firstTargetDifference=row)),flush=True)
            steps.append(row);last_colors[handle]=raw
        pending=None;index=b'';instances=b'';last_event=None;repetitions=0;semantic_clear=None
        def submit():
            nonlocal draws,pending,index,instances,repetitions,active_uv
            if pending is None:return
            w=pending['words'];assert w[121]==pending['blob']['bytes']and w[123]==len(index)and w[124]==len(instances)
            expected_repetitions=len(instances)//68 if instances else 1;assert repetitions==expected_repetitions
            before=len(allocations)
            if draws+1 in args.probe_draw:
                assert not index and not instances
                pointer=call('gpu_probe',words(w),upload(blob(pending['blob'])));assert pointer and gl_error()==0
                (out/('draw-'+str(draws+1)+'-source.rgba32f')).write_bytes(memory.read(store,pointer,pointer+640*480*16))
                if args.uv_probe:
                    active_uv=True
                    try:pointer=call('gpu_probe',words(w),upload(blob(pending['blob'])))
                    finally:active_uv=False
                    assert pointer and gl_error()==0
                    (out/('draw-'+str(draws+1)+'-uv.rgba32f')).write_bytes(memory.read(store,pointer,pointer+640*480*16))
            assert call('gpu_issue',words(w),upload(blob(pending['blob'])),upload(index),upload(instances))==1
            for pointer in allocations[before:]:call('gpu_release',pointer)
            del allocations[before:];assert gl_error()==0
            draws+=expected_repetitions;compare(last_event,w[1],w);pending=None
        for row in trace['events']:
            kind=row['kind'];w=[v&0xffffffff for v in row['words']]
            if kind==1:
                submit();pending=row;index=b'';instances=b'';repetitions=0
            elif kind==2:index=blob(row['blob'])
            elif kind==3:instances=blob(row['blob'])
            elif kind==101:last_event=row['sequence'];repetitions+=1
            elif kind==10:submit();semantic_clear=row
            elif kind==110:
                assert semantic_clear and w[:4]==semantic_clear['words'][:4]
                before=len(allocations);assert call('gpu_clear',words(w),words(semantic_clear['words'][6:10]),words(row['rectangles']),w[6])==1
                for pointer in allocations[before:]:call('gpu_release',pointer)
                del allocations[before:];assert gl_error()==0;clears+=1;compare(row['sequence'],w[0])
            elif kind==20:submit();assert w[0]==1
            else:assert kind in [4,120],kind
        submit();assert draws==expected_draws and clears==expected_clears
        raw=read(1);(out/'frame.bgra').write_bytes(raw);baseline=args.baseline.read_bytes();baseline_exact=raw==baseline
        assert baseline_exact,'Semantic replay must reproduce every byte of the explicitly selected complete baseline'
        completed=True
    except BaseException as failure:error=repr(failure);raise
    finally:
        context.close()
        report=dict(completed=completed,error=error,completeBufferBaselineExact=baseline_exact,baselineKind=args.baseline_kind,
            actualApplicationBaselineExact=baseline_exact and args.baseline_kind=='current-application',actualSemanticBatches=len([r for r in trace['events']if r['kind']==1]),
            representedNativeDraws=draws,actualClears=clears,steps=steps,firstDifferingTargets=sorted(first_targets),
            sourceTraceSha256=SHA(trace_raw),nativeComparisonsSha256=SHA(native_raw),wasmSha256=SHA(wasm),
            toolSha256=SHA(Path(__file__).read_bytes()),initialGpuColorsObserved=True,rendererCppChanged=not build.get('originalRendererSourcesUnmodified',True),
            diagnosticPrivateAccessOnly=True,glCalls=dict(calls),nativeEqualityAccepted=False,browserAcceptance=False,completeGame=False)
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');(out/'shaders.json').write_text(json.dumps(shaders,indent=2)+'\n')
        print(json.dumps({k:report[k]for k in ['completed','error','actualApplicationBaselineExact','representedNativeDraws','firstDifferingTargets']}),flush=True)
        storage.check_budget(out,100*1024**3,128*1024**2)


if __name__=='__main__':main()
