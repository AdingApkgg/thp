"""Verify the role/alignment correction changes comments, not the shipped program."""
from pathlib import Path
import hashlib,json,os,subprocess,sys
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/camera-roles-nov12-v3';O=H/'comment-objects';O.mkdir(exist_ok=False)
load=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();change=load(H/'comment-only-source-change.json')
old=(H/'SceneCompositor-before-comment.hpp').read_bytes();new=(R/change['path']).read_bytes();before=b"// Retail's shared world camera and its right XY qword are 8-byte aligned.";after=b"// Keep shared right XY naturally aligned for Wasm's qword atomic access."
assert old.replace(before,after)==new and old.count(before)==1 and old.count(b'\n')==new.count(b'\n')
assert sha(H/'SceneCompositor-before-comment.hpp')==change['beforeSha256'] and sha(R/change['path'])==change['afterSha256']
parent=load(R/'artifacts/th14/camera-right-pair-nov12/current-provider-bindings.json');browser=load(R/'artifacts/th14/camera-right-pair-nov12/browser/build.json');source=R/'runtimes/th12/th12_web/cpp/game/SceneCompositor.cpp';results=[]
for mode in ['sdk','browser']:
    obj=O/(mode+'.o');env={**os.environ,'TEMP':str(O),'TMP':str(O),'TMPDIR':str(O)}
    if mode=='sdk':
        cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(cc)==parent['compilerSha256'];cmd=[str(cc),*parent['flags'],'-c',str(source),'-o',str(obj)];expected=next(r['objectSha256'] for r in parent['currentProviders'] if Path(r['source']).name=='SceneCompositor.cpp')
    else:
        sdk=R/'runtimes/th12/tools/emsdk';cc=sdk/'upstream/emscripten/emcc.py';assert sha(cc)==browser['compilerSha256'];env.update(EM_CONFIG=str(sdk/'.emscripten'),EMSDK=str(sdk),EMSDK_PYTHON=sys.executable,EMCC_CORES='2');cmd=[sys.executable,str(cc),*browser['flags'],'-c',str(source),'-o',str(obj)];expected=next(r['sha256'] for r in browser['objects'] if Path(r['source']).name=='SceneCompositor.cpp')
    with (O/(mode+'.log')).open('wb') as log:subprocess.run(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120,env=env)
    assert sha(obj)==expected,(mode,sha(obj),expected);results.append(dict(backend=mode,objectByteIdentical=True,sha256=expected))
bindings=dict(parent['sourceBindings']);assert bindings[change['path']]==change['beforeSha256'];bindings[change['path']]=change['afterSha256']
for p,d in bindings.items():assert sha(R/p)==d,p
current=dict(parent);current.update(sourceBindings=bindings,providerActualSourceBindings=parent['sourceBindings'],semanticNoOpSourceRebindings=[dict(**change,proofPath='artifacts/th14/camera-roles-nov12-v3/comment-objects/checked.json')],compiledSourcesWereBeforeThisCommentCorrection=True,exactByteIdentityIsNotClaimedForChangedCommentHeader=True)
(H/'current-provider-bindings.json').write_text(json.dumps(current,indent=2)+'\n')
report=dict(sourceCommentCorrection=change,checks=results,preprocessorTokensAndLinePositionsUnchangedBySingleCommentReplacement=True,
    allOtherSourceBytesIdentical=True,currentSourceFiles=368,alreadyCompiledOtherProvidersNotRecompiled=True,
    productionRuntimeSourceCommit='572751a813eb58c874c901e20040b7674b1b8dcd',productionWasmSha256='9b17c2e2bfe2e19a63af3b6d2c7d0ba6082ca05f24bef858ab51f85d65e022b4',
    runtimeRebuilt=False,runtimeRedeployed=False,newGameRuns=0,newGpuRuns=0,wholeGameAccepted=False,completeGame=False)
(O/'checked.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
