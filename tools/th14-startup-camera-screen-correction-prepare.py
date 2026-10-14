"""Freeze the one-file TH14 screen correction and prepare a four-camera control."""
import hashlib,json,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RT=ROOT/'runtimes/th12/th12_web'
OUT=ROOT/'artifacts/th14/startup-camera-screen-correction-prepared-oct14'
OLD=ROOT/'artifacts/th14/startup-camera-same-input-math-prepared-oct14'
ACTUAL=ROOT/'artifacts/th14/startup-viewport-original-owner-prefix-prepared-oct14/run-oct14/report.json'
ACTUAL_SHA='ea77520cdab9bfb35ba0905b416f42c78af597b401bbfd13c8715424b6a3341e'
VIEWPORTS=ROOT/'artifacts/th14/compositor-native.json'
COMPILER=ROOT/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
RUNNER=ROOT/'tools/th14-startup-camera-screen-correction-check.mjs'
BEFORE_SHA='72a5b43fb397885086f65083cc13d22971bda2b7632c516df91301ed6d6c1e93'
MATH_SHA='b159b3d617a522977c795351b5ff56338d5058b899ab984a590c8b50f8a9fd6e'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def bind(path):
    raw=path.read_bytes();return dict(path=path.resolve().as_posix(),bytes=len(raw),sha256=sha(raw))
def verify(b):
    raw=Path(b['path']).read_bytes()
    if len(raw)!=b['bytes'] or sha(raw)!=b['sha256']:raise ValueError('binding changed: '+b['path'])
    return raw
def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
    return bind(path)
def raw_float(value):return struct.unpack('<I',struct.pack('<f',value))[0]
def main():
    if (OUT/'inputs.json').exists() or (OUT/'plan.json').exists():raise RuntimeError('preserve existing preparation')
    before=OUT/'before/cpp/game/SceneCamera.cpp';before_raw=before.read_bytes()
    after=RT/'cpp/game/SceneCamera.cpp';after_raw=after.read_bytes()
    if sha(before_raw)!=BEFORE_SHA or sha((RT/'cpp/game/GraphicsMath.cpp').read_bytes())!=MATH_SHA:raise ValueError('unexpected source basis')
    marker=b'#else\n';begin=after_raw.index(b'#if PORT_TITLE == 14',after_raw.index(b'void SceneCamera::screen()'))
    old_branch=after_raw[after_raw.index(marker,begin)+len(marker):after_raw.index(b'#endif',begin)]
    old_body=before_raw[before_raw.index(b'    const float width=',before_raw.index(b'void SceneCamera::screen()')):before_raw.index(b'\n}',before_raw.index(b'void SceneCamera::screen()'))+1]
    if old_branch!=old_body:raise ValueError('non-TH14 original body changed')
    before_prefix=before_raw[:before_raw.index(b'void SceneCamera::screen()')]
    if after_raw[:after_raw.index(b'void SceneCamera::screen()')]!=before_prefix:raise ValueError('non-screen source changed')
    raw=ACTUAL.read_bytes()
    if sha(raw)!=ACTUAL_SHA:raise ValueError('proper viewport actual report changed')
    actual=json.loads(raw);calls=actual['originalD3dxMathCalls']
    if len(calls)!=8 or actual['pendingD3dxMathCalls']:raise ValueError('eight completed original calls required')
    if actual['declaredFpuState']!=dict(fpcw=0x37f,mxcsr=0x1f80,nativeMeasured=False):raise ValueError('FPU baseline changed')
    owner=actual['originalPreCallbackInitializers'][1]
    if owner['afterWords']['0x4f7a64']!=640 or owner['afterWords']['0x4f7a68']!=480 or owner['afterWords']['0x4f7a6c']!=0x3f800000:raise ValueError('proper viewport dimensions required')
    observed=json.loads(VIEWPORTS.read_text(encoding='utf-8'))
    if observed['executableSha256']!='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353':raise ValueError('viewport oracle executable')
    matches=[r for r in observed['cameras'] if r['width']==640 and r['height']==480 and r['scale']==1]
    if len(matches)!=1:raise ValueError('one exact original viewport row required')
    viewports=matches[0]['viewports'];map_indices=[2,0,1,3];offsets=[0x488,0x230,0x35c,0x5b4];modes=[2,2,1,3]
    input_words=[];parameter_words=[];oracle=[];cases=[]
    for index,(old_index,offset,mode) in enumerate(zip(map_indices,offsets,modes)):
        look,projection=calls[index*2:index*2+2];camera=0x4d8f60+offset
        if look['outputPointer']!=camera+0x60 or projection['outputPointer']!=camera+0xa0:raise ValueError('actual camera owner does not map to original reset viewport')
        if look['function']!='D3DXMatrixLookAtLH' or projection['function']!='D3DXMatrixPerspectiveFovLH':raise ValueError('unexpected original calls')
        if not all(c['originalReturnVerified'] and c['hostMathResultWrites']==0 for c in [look,projection]):raise ValueError('original arithmetic boundary incomplete')
        v=viewports[old_index]
        if len(v)!=6 or any(type(w) is not int for w in v[:4]):raise ValueError('raw integer viewport fields required')
        words=list(v[:4])+[raw_float(v[4]),raw_float(v[5]),projection['arguments'][1],mode]
        params=sum(look['inputVectorWords'],[])+projection['arguments'][1:]
        outputs=look['afterWords']+projection['afterWords']
        if len(words)!=8 or len(params)!=13 or len(outputs)!=32:raise ValueError('fixed record shape')
        input_words+=words;parameter_words+=params;oracle+=outputs
        cases.append(dict(index=index,owner=camera,viewportEvidenceRow=old_index,viewportWords=words[:6],inputWords=words,oracleParameterWords=params,oracleMatrixWords=outputs,actualMathCallIndices=[index*2,index*2+1]))
    basis_path=OLD/'current-production-bindings.json';basis=json.loads(basis_path.read_text(encoding='utf-8'))
    if len(basis['sources'])!=267 or len(basis['objects'])!=141:raise ValueError('current267/141 before-change basis required')
    current_sources=[]
    for b in basis['sources']:
        if Path(b['path']).resolve()==after.resolve():
            if b['sha256']!=BEFORE_SHA:raise ValueError('before-change source provenance')
            current_sources.append(bind(after))
        else:verify(b);current_sources.append(b)
    for b in basis['objects']:verify(b)
    production=save(OUT/'production-source-bindings.json',dict(beforeBasis=bind(basis_path),beforeSource=bind(before),correctedProductionSource=bind(after),currentSourceFiles=267,sourceFilesChanged=1,currentSources=current_sources,engineObjectsBeforeRebuild=141,beforeObjects=basis['objects'],engineObjectsRebuiltByPreparation=0,productionObjectsLinkedByControl=0))
    seen=set();frozen=[]
    def freeze(path):
        path=path.resolve()
        if path in seen:return
        seen.add(path);relative=path.relative_to(RT.resolve()).as_posix();data=path.read_bytes()
        before_data=before_raw if relative=='cpp/game/SceneCamera.cpp' else data
        entries={}
        for mode,data_to_copy in [('before',before_data),('after',data)]:
            destination=OUT/mode/relative;destination.parent.mkdir(parents=True,exist_ok=True)
            if destination.exists():
                if destination.read_bytes()!=data_to_copy:raise ValueError('existing frozen source differs')
            else:
                with destination.open('xb') as f:f.write(data_to_copy)
            entries[mode]=bind(destination)
        frozen.append(dict(original=bind(path),**entries))
        for include in re.findall(r'^\s*#\s*include\s*"([^"]+)"',data.decode(),re.M):freeze(path.parent/include)
    freeze(after);freeze(RT/'cpp/game/GraphicsMath.cpp')
    inputs=save(OUT/'inputs.json',dict(schema='th14-screen-correction-control-input-v1',actualReport=bind(ACTUAL),originalViewportEvidence=bind(VIEWPORTS),declaredOriginalD3dxFpu=actual['declaredFpuState'],cases=cases,inputWords=input_words,oracleParameterWords=parameter_words,oracleMatrixWords=oracle,
        ownerMappingScope='Same original4465e0 reset: full+488, play+230, scaled+35c, world+5b4. Viewport integers/depth come from the existing original reset640x480/scale1 observation; fresh actual D3DX call destinations and original inputs/outputs bind each owner. Mode is declared from the original reset copies and is unused by screen(). No SceneCompositor construction equivalence is claimed.',
        originalArithmetic=dict(center='float32(origin)+float32(float32(size)*0.5); no integer truncation of center',distanceNumerator='float32(u32 viewport.height>>1)',tangent='float32(tan(double(float32(camera.fov*0.5))))',distance='float32 distance numerator / float32 tangent',projectionFov='camera.fov',nearPlaneWord=0x3f800000,farPlaneWord=0x461c4000),
        scope='Four real SceneCamera.screen calls before/after the TH14-only source correction; instrumented GraphicsMath observers forward unchanged parameters to the real mathematics. Parameter52words and matrix128words compare with pinned original D3DX baseline. No Native CPU, draw/GPU, other-title runtime or whole-game equality.'))
    run_dir=OUT/'run-oct14';builds=[]
    flags=['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=14','-Wl,--wrap=_ZN4th1112GraphicsMath7look_atENS_4Vec3ES1_S1_','-Wl,--wrap=_ZN4th1112GraphicsMath11perspectiveEffff']
    for mode in ['before','after']:
        source=OUT/mode/'cpp/game';wasm=run_dir/(mode+'.wasm')
        args=flags+['-I'+source.as_posix(),(source/'SceneCamera.cpp').as_posix(),(source/'GraphicsMath.cpp').as_posix(),(OUT/'fixture.cpp').as_posix(),'-o',wasm.as_posix()]
        builds.append(dict(mode=mode,compilerArguments=args,wasmPath=wasm.as_posix()))
    required=[bind(Path(__file__)),bind(RUNNER),bind(OUT/'fixture.cpp'),inputs,production,bind(ACTUAL),bind(VIEWPORTS),bind(COMPILER)]+[d[m] for d in frozen for m in ['before','after']]
    plan=save(OUT/'plan.json',dict(schema='th14-screen-correction-control-plan-v1',prepared=True,compiler=bind(COMPILER),builds=builds,runDirectory=run_dir.as_posix(),inputs=inputs,productionBindings=production,frozenSources=frozen,requiredBindings=required,exports=['memory','_initialize','input_buffer','parameter_buffer','matrix_buffer','run_screen'],inputBytes=128,parameterBytes=208,matrixBytes=512,executionCounts=dict(compiles=0,wasi=0,originalX86=0,browser=0,audio=0),futureCommand='C:/nvm4w/nodejs/node.exe tools/th14-startup-camera-screen-correction-check.mjs --execute',scope='Future two tiny WASI reactors: the unchanged before source and the one TH14-only corrected SceneCamera.cpp, each with frozen GraphicsMath.cpp and identical fixture. No production object rebuild or old evidence overwrite.'))
    receipt=save(OUT/'preparation-receipt.json',dict(prepared=True,executed=False,productionSourceChanged=True,productionFilesChanged=1,beforeSource=bind(before),afterSource=bind(after),mathSourceUnchangedSha256=MATH_SHA,nonTh14OriginalBranchByteEqual=True,nonScreenOriginalPrefixByteEqual=True,baselineSourceFiles=267,unchangedBaselineSources=266,engineObjectsBeforeRebuildVerified=141,engineObjectsRebuilt=0,minimalDependencyFiles=len(frozen),cases=4,parameterWords=52,matrixWords=128,inputs=inputs,plan=plan,productionBindings=production,fixture=bind(OUT/'fixture.cpp'),runner=bind(RUNNER),prepareTool=bind(Path(__file__)),executionCounts=dict(compiles=0,wasi=0,originalX86=0,browser=0,audio=0),scope='One authorized production screen() TH14-only correction and pure source/input preparation. No C++/WASI/original execution or comparison verdict. Other title original screen body remains byte-identical.'))
    print(json.dumps(dict(inputs=inputs,plan=plan,receipt=receipt,correctedSource=bind(after),dependencies=len(frozen))))
if __name__=='__main__':main()
