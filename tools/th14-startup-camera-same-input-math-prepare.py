"""Prepare frozen same-input math evidence; never compile or execute any runtime."""
import hashlib
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RT=ROOT/'runtimes/th12/th12_web'
OUT=ROOT/'artifacts/th14/startup-camera-same-input-math-prepared-oct14'
ACTUAL=ROOT/'artifacts/th14/startup-viewport-original-owner-prefix-prepared-oct14/run-oct14/report.json'
ACTUAL_SHA='ea77520cdab9bfb35ba0905b416f42c78af597b401bbfd13c8715424b6a3341e'
BASIS=ROOT/'docs/porting/th14-staged-loader-current-checkpoint-oct14.json'
OBJECT_ROOT=ROOT/'runtimes/th13/th13_web/artifacts/cpp/objects-th14'
RUNNER=ROOT/'tools/th14-startup-camera-same-input-math-check.mjs'
COMPILER=ROOT/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'

def digest(raw):return hashlib.sha256(raw).hexdigest()
def bind(path):
    raw=path.read_bytes()
    return dict(path=path.resolve().as_posix(),bytes=len(raw),sha256=digest(raw))
def write_new(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    raw=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    with path.open('xb') as f:f.write(raw)
    return bind(path)
def checked_words(words,count):
    if not isinstance(words,list) or len(words)!=count or any(type(w) is not int or not 0<=w<=0xffffffff for w in words):
        raise ValueError('invalid observed raw32 words')
    if any((w&0x7f800000)==0x7f800000 for w in words):raise ValueError('finite proper-viewport inputs/output required')
    return list(words)

def main():
    if (OUT/'inputs.json').exists() or (OUT/'plan.json').exists():raise RuntimeError('prepared output already exists; no overwrite')
    actual_raw=ACTUAL.read_bytes()
    if digest(actual_raw)!=ACTUAL_SHA:raise ValueError('actual original-prefix report changed')
    actual=json.loads(actual_raw)
    if actual['declaredFpuState']!=dict(fpcw=0x37f,mxcsr=0x1f80,nativeMeasured=False):raise ValueError('unexpected declared D3DX FPU profile')
    calls=actual['originalD3dxMathCalls']
    if len(calls)!=8 or actual['pendingD3dxMathCalls']:raise ValueError('eight completed calls required')
    cases=[];packed=[];oracle=[]
    for index,call in enumerate(calls):
        expected='D3DXMatrixLookAtLH' if index%2==0 else 'D3DXMatrixPerspectiveFovLH'
        if call['function']!=expected or not call['originalReturnVerified'] or call['hostMathResultWrites']!=0:raise ValueError('unverified original math call')
        if call['outputBytes']!=64 or call['returnedRegisters']['eax']!=call['outputPointer']:raise ValueError('original output ABI mismatch')
        if index%2==0:
            vectors=call['inputVectorWords']
            if len(vectors)!=3:raise ValueError('three original vector inputs required')
            input_words=[1]+sum([checked_words(v,3) for v in vectors],[])+[0,0]
        else:
            if len(call['arguments'])!=5:raise ValueError('original perspective argument count')
            input_words=[2]+checked_words(call['arguments'][1:],4)+[0]*7
        outputs=checked_words(call['afterWords'],16)
        packed+=input_words;oracle+=outputs
        cases.append(dict(index=index,function=expected,originalCallAddress=call['callAddress'],originalIat=call['iat'],originalTarget=call['target'],originalOutputPointer=call['outputPointer'],inputWords=input_words,oracleWords=outputs,inputVectorWords=call.get('inputVectorWords'),originalArguments=call['arguments'],returnedRegisters=call['returnedRegisters']))
    if len(packed)!=96 or len(oracle)!=128:raise ValueError('fixed input/output size')
    basis=json.loads(BASIS.read_text(encoding='utf-8'))
    if basis['sourceFilesVerified']!=267 or basis['engineObjectsVerified']!=141 or len(basis['sourceHashes'])!=267 or len(basis['objectHashes'])!=141:raise ValueError('current267/141 basis required')
    source_bindings=[]
    for name,expected in sorted(basis['sourceHashes'].items()):
        info=bind(RT/name)
        if info['sha256']!=expected:raise ValueError('current production source differs from267 basis: '+name)
        source_bindings.append(info)
    object_bindings=[]
    for name,expected in sorted(basis['objectHashes'].items()):
        info=bind(OBJECT_ROOT/(name.replace('/','_')+'.o'))
        if info['sha256']!=expected:raise ValueError('current engine object differs from141 basis: '+name)
        object_bindings.append(info)
    production=write_new(OUT/'current-production-bindings.json',dict(sourceFilesVerified=267,engineObjectsVerified=141,basisReceipt=bind(BASIS),sources=source_bindings,objects=object_bindings,objectsLinkedByThisControl=0))
    seen=set();frozen=[]
    def freeze(path):
        path=path.resolve()
        if path in seen:return
        seen.add(path)
        relative=path.relative_to(RT.resolve()).as_posix()
        if relative not in basis['sourceHashes']:raise ValueError('include outside267 source basis: '+relative)
        raw=path.read_bytes()
        if digest(raw)!=basis['sourceHashes'][relative]:raise ValueError('source changed during freeze')
        destination=OUT/'source'/relative;destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('xb') as f:f.write(raw)
        frozen.append(dict(original=bind(path),frozen=bind(destination)))
        for include in re.findall(r'^\s*#\s*include\s*"([^"]+)"',raw.decode('utf-8'),re.M):freeze(path.parent/include)
    freeze(RT/'cpp/game/GraphicsMath.cpp')
    inputs=write_new(OUT/'inputs.json',dict(schema='th14-original-camera-same-input-math-v1',actualReport=bind(ACTUAL),declaredOriginalD3dxFpu=actual['declaredFpuState'],pinnedD3dx=actual['pinnedD3dx']['image'],dispatchBaseline=actual['pinnedD3dx']['initialDispatchCopy'],cases=cases,inputWords=packed,oracleWords=oracle,caseCount=8,inputWordCount=96,outputWordCount=128,scope='Same observed raw32 D3DX LookAt/Perspective inputs to current GraphicsMath only. Original pinned DLL dispatch/FPCW37f is a declared baseline; no measured Native CPU overlay, SceneCompositor initialization, Renderer, GPU or whole-game equivalence.'))
    run_dir=OUT/'run-oct14';wasm=run_dir/'math.wasm'
    args=['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=14',(OUT/'source/cpp/game/GraphicsMath.cpp').as_posix(),(OUT/'fixture.cpp').as_posix(),'-o',wasm.as_posix()]
    required=[bind(Path(__file__)),bind(RUNNER),bind(OUT/'fixture.cpp'),production,inputs,bind(BASIS),bind(ACTUAL),bind(COMPILER)]+[f['frozen'] for f in frozen]
    plan=write_new(OUT/'plan.json',dict(schema='th14-camera-same-input-math-plan-v1',prepared=True,executionAuthorizedByThisPreparation=False,executionCounts=dict(compiles=0,wasi=0,originalX86=0,nativeProcesses=0,browser=0,audio=0),compiler=bind(COMPILER),compilerArguments=args,runDirectory=run_dir.as_posix(),inputs=inputs,productionBindings=production,frozenSources=frozen,requiredBindings=required,exportContract=['input_buffer','output_buffer','run_math','memory','_initialize'],inputBytes=384,outputBytes=512,futureCommand='C:/nvm4w/nodejs/node.exe tools/th14-startup-camera-same-input-math-check.mjs --execute',scope='Future one compile of frozen GraphicsMath.cpp plus fixture.cpp; eight same-input math calls only. Does not link any of the141 production objects. No original execution, OS audio, SDL, browser, renderer or default-screen input comparison.'))
    receipt=write_new(OUT/'preparation-receipt.json',dict(prepared=True,executed=False,actualReport=bind(ACTUAL),productionBindings=production,currentProductionSourcesVerified=267,currentEngineObjectsVerified=141,objectsLinked=0,frozenDependencyFiles=len(frozen),inputs=inputs,plan=plan,fixture=bind(OUT/'fixture.cpp'),prepareTool=bind(Path(__file__)),runner=bind(RUNNER),caseCount=8,oracleWords=128,executionCounts=dict(compiles=0,wasi=0,originalX86=0,browser=0,nativeProcesses=0,audio=0),scope='Pure input extraction, original-byte source freezing and hash verification. No fixture, compiler, WASI, Native or model execution; no comparison verdict yet.'))
    print(json.dumps(dict(inputs=inputs,plan=plan,receipt=receipt,frozenDependencyFiles=len(frozen)),ensure_ascii=False))

if __name__=='__main__':main()
