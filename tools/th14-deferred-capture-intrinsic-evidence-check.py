"""Freeze intrinsic manager queue prototype, source isolation and syntax proof."""
import hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/th14/deferred-capture-intrinsic-oct14';V1=ROOT/'artifacts/th14/deferred-capture-integration-oct14';evidence={}
sha=lambda b:hashlib.sha256(b).hexdigest()
def track(p):
    p=Path(p);p=p if p.is_absolute() else ROOT/p;b=p.read_bytes();evidence[p.relative_to(ROOT).as_posix()]={'bytes':len(b),'sha256':sha(b)};return b
def read(p):return json.loads(track(p))
inputs=read(OUT/'intrinsic-inputs.json');code=read('docs/porting/th14-deferred-capture-intrinsic-code-verified-oct14.json');vmclear=read('docs/porting/th14-deferred-capture-vm-clear-verified-oct14.json')
assert inputs['privateIntrinsicPrepared'] and code['privateIntrinsicCodeVerified'] and vmclear['diagnosticEvidenceVerified']
assert inputs['toolSha256']==sha(track('tools/th14-deferred-capture-intrinsic-build.py'))
assert code['toolSha256']==sha(track('tools/th14-deferred-capture-intrinsic-check.mjs'))
assert code['inputsSha256']==sha(track(OUT/'intrinsic-inputs.json')) and code['wasmSha256']==sha(track(OUT/'intrinsic.wasm'))
assert code['fixtureSha256']==sha(track(OUT/'fixture.cpp'))
for p,b in inputs['sourceFiles'].items():assert sha(track(OUT/'source'/p))==b['sha256']
for p,b in inputs['sourceBindings'].items():
    selected=OUT/('before' if p in inputs['modifiedExistingFiles'] else 'source')/p
    assert sha(track(selected))==b['sha256']
assert inputs['patchSha256']==sha(track(OUT/'intrinsic.patch'))
assert vmclear['toolSha256']==sha(track('tools/th14-deferred-capture-vm-clear-evidence-check.py'))
assert vmclear['captureRecordsComparedBytes']==640 and all(not r['captureRecordWrites'] and not r['callsExecuted'] for r in vmclear['fullOrdinaryPooledVmDestroyCases'])
control=code['intrinsicControls'];assert control['newManagerFiles']==[-1]*4 and not control['captureStaticRegistryUsed']
assert control['beforeVmClear160Words']==control['afterVmClear160Words'] and control['beforeVmClear160Words'][0]==0
assert [control['firstSlotNegativeWithOtherPending160Words'][i] for i in [0,10,20,30]]==[-1,0,1,25]
assert [control['afterAllSlotsHeadless160Words'][i] for i in [0,10,20,30]]==[-1]*4
assert control['explicitHeadlessRetirement'] and code['managerQueueSurvivesMenuDestruction']
assert len(code['cases'])==7 and len(code['retirements'])==6 and len(code['immediateSourceCases'])==6
rt=ROOT/'runtimes/th12/th12_web';python='C:/Users/APKGG/AppData/Local/Programs/Python/Python314/python.exe'
command=[str(ROOT/'runtimes/th12/tools/emsdk/upstream/emscripten/emcc.py'),'-fsyntax-only','-std=c++17','-DPORT_TITLE=14','--use-port=sdl3','-I',str(OUT/'source/cpp/game'),'-I',str(OUT/'source/cpp/sdl'),'-I',str(rt/'cpp/sdl'),'-I',str(rt/'cpp/game'),str(OUT/'source/cpp/sdl/Application.cpp')]
syntax=subprocess.run([python,*command],cwd=ROOT,capture_output=True,text=True);assert syntax.returncode==0,syntax.stderr
syntax_path=OUT/'application-syntax.json';syntax_path.write_text(json.dumps(dict(returncode=syntax.returncode,arguments=command,stdout=syntax.stdout,stderr=syntax.stderr),indent=2)+'\n',encoding='utf8');track(syntax_path)
# Prove unchanged non14 tokens across the entire actual Pause translation
# units and Manager header. Normalize only the relocated private __FILE__ paths.
compiler=ROOT/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';tokens=lambda s:re.findall(r'"(?:\\.|[^"\\])*"|\w+|[^\s]',s)
isolations=[]
for title in [12,16]:
    for relative in ['cpp/game/PauseMenu.cpp','cpp/game/PauseEnd.cpp','cpp/game/AnmManager.hpp']:
        outputs=[];arguments=[]
        for root_path in [rt,OUT/'source']:
            args=[str(compiler),'--target=wasm32-wasip1','-std=c++17','-E','-P','-DPORT_TITLE='+str(title),'-I',str(root_path/'cpp/game'),'-I',str(rt/'cpp/game'),'-I',str(rt/'cpp/sdl'),'-x','c++',str(root_path/relative)]
            result=subprocess.run(args,cwd=ROOT,capture_output=True,text=True);assert result.returncode==0,result.stderr
            normalized=result.stdout.replace(str(OUT/'source').replace('\\','/'),str(rt).replace('\\','/')).replace(str(OUT/'source'),str(rt))
            outputs.append(tokens(normalized));arguments.append(args[1:])
        assert outputs[0]==outputs[1],(title,relative)
        isolations.append(dict(title=title,translationUnit=relative,preprocessedTokenCount=len(outputs[0]),preprocessedTokensSha256=sha(json.dumps(outputs[0],ensure_ascii=False).encode()),privateTokensEqualOriginal=True,arguments=arguments))
header=track(OUT/'source/cpp/game/AnmManager.hpp').decode('utf8');app=track(OUT/'source/cpp/sdl/Application.cpp').decode('utf8');end=track(OUT/'source/cpp/game/PauseEnd.cpp').decode('utf8');helper=track(OUT/'source/cpp/sdl/ApplicationCaptureTh14.hpp').decode('utf8')
assert 'DeferredCaptureQueueTh14 deferred_captures;' in header and 'first_deferred_capture_file_index()const noexcept{return deferred_captures.first_file_index();}' in header
assert header.index('u32 next_id=0,spawn_depth=0;')<header.index('DeferredCaptureQueueTh14 deferred_captures;')
assert 'auto& queue=animations.deferred_captures;' in end
assert app.index('if(!session.draw(renderer,&frame_text))')<app.index('th14_consume_deferred_captures(session.animations.deferred_captures,session,graphics,renderer);')<app.index('graphics.present();')
assert 'renderer.flush();\n        th14_consume_deferred' not in app
assert 'if(!target)return;' in helper and 'queue.consume' in helper and 'graphics.backend.resample' in helper
assert 'th14_capture_bindings' not in header+app+end+helper and 'DeferredCaptureBindingTh14' not in header+app+end+helper
assert (OUT/'source/cpp/game/AnmManager.cpp').read_bytes()==(V1/'source/cpp/game/AnmManager.cpp').read_bytes()
out=dict(privateIntrinsicEvidenceVerified=True,productionChanged=False,productionAdopted=False,completeGame=False,nativeEquivalent=False,
 actualPrivateMenuEntryCases=7,controlledBackendRetirements=6,typedImmediateSourceCases=6,ordinaryNativeVmDestroyPreservedBytes=640,
 applicationSyntaxPassed=True,non14PreprocessedTokenIsolation=isolations,captureStaticRegistryUsed=False,
 loaderFirstSlotGetter='session.animations.first_deferred_capture_file_index()',postDrawQueue='session.animations.deferred_captures',headlessExplicitNoTargetRetirement='session.animations.retire_deferred_captures_without_target()',
 modifiedExistingFiles=inputs['modifiedExistingFiles'],newHelpers=['cpp/game/DeferredCaptureQueueTh14.hpp','cpp/sdl/ApplicationCaptureTh14.hpp'],patchSha256=inputs['patchSha256'],intrinsicControls=control,evidence=evidence,toolSha256=sha(Path(__file__).read_bytes()),
 scope='Reviewable private intrinsic queue prototype. Actual original resource parsing and private Pause/Manager methods run with controlled copy return/target boundaries. Native ordinary pooled-VM destroy separately preserves queued160B records. Header field is appended after existing manager fields; whole production rebuild is required for enclosing GameSession layout. SDL Application is syntax-checked, not fully executed here. No ROOT/loading private copies are changed. No static queue registration, generic resource-owner guess, boot-upload substitution, capture mask, Native GPU completion simulation or pixel/whole-game equivalence claim. Root must merge only small reviewed hunks with loading changes and perform current production full builds/replays/GPU tests.')
report=ROOT/'docs/porting/th14-deferred-capture-intrinsic-verified-oct14.json';report.write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
done=dict(reportSha256=sha(report.read_bytes()),codeReportSha256=sha(track('docs/porting/th14-deferred-capture-intrinsic-code-verified-oct14.json')),patchSha256=inputs['patchSha256'],toolSha256=out['toolSha256'])
completion=OUT/'intrinsic-complete.json'
if completion.exists():assert json.loads(completion.read_bytes())==done
else:completion.write_text(json.dumps(done,indent=2)+'\n',encoding='utf8')
print(json.dumps({'privateIntrinsicEvidenceVerified':True,'applicationSyntaxPassed':True,'non14TokenIsolations':len(isolations),'captureStaticRegistryUsed':False,'productionAdopted':False}))
