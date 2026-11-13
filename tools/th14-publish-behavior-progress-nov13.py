"""Publish an explicit source/doc allowlist via Git blobs and SHA-only tree."""
from pathlib import Path
import base64,hashlib,json,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/behavior-matrix-nov13';O=H/'publication';assert not O.exists();O.mkdir()
gh='C:/Program Files/GitHub CLI/gh.exe';repo='repos/AdingApkgg/thp'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_bytes())
assert load(H/'qualified-30.json')['allDeclaredCasesPassed']and load(H/'gpu-matrix-report.json')['passed']
assert load(H/'gpu-tail-c2-s0-d1-v2/report.json')['passed']
browser=load(H/'browser/build.json');normal=load(R/'artifacts/th14/current-normal-full-nov13/raw-audit.json')
assert normal['selected32Hud2Cursor4Exact']and normal['completeEncodedScoreExact']and normal['completeDecodedScoreExact']
for n,h in browser['sourceBindings'].items():assert sha(R/n)==h,n
summary=dict(acceptanceStandard='observable-behavior-alignment',latestUserRequirementSupersedesBitExactOneToOne=True,
 normalFullCallbacks=122005,normalMeasuredGameRngHudCursorsExact=True,normalEncodedAndDecodedScoresExact=True,
 strictNormal113StillFalse=True,strictNormalCameraDifferentRows=16616,ordinaryFunctionalCases=24,extraFunctionalCases=6,
 extraUsesControlledExternalUnlockedSave=True,ordinaryUnlockProgressionAccepted=False,
 actualGpuNormalLoadouts=6,actualGpuCapturedFrames=24,sakuyaAPostBomb120FrameDisplayRestored=True,
 allMeasuredWorkersDevicesClockRetired=True,audibleOutput=False,
 browserWasmSha256=browser['sha256'],browserLoaderSha256=browser['loaderSha256'],browserFreshUnits=2,browserVerifiedReusedObjects=144,
 browserUiAccepted=False,deployed=False,fullAllModeReplaysAccepted=False,allOrdinaryFlowsAndSavesAccepted=False,completeGame=False,
 sourceChanges=browser['sourceChanges'],evidence={n:sha(R/n)for n in [
 'artifacts/th14/current-normal-full-nov13/raw-audit.json','artifacts/th14/behavior-matrix-nov13/qualified-30.json',
 'artifacts/th14/behavior-matrix-nov13/gpu-matrix-report.json','artifacts/th14/behavior-matrix-nov13/gpu-tail-c2-s0-d1-v2/report.json',
 'artifacts/th14/behavior-matrix-nov13/browser/build.json']})
public=R/'docs/porting/th14-behavior-progress-nov13.json';assert not public.exists();public.write_text(json.dumps(summary,indent=2)+'\n')
files=[
 'runtimes/th12/portable/sdl/Renderer.cpp','runtimes/th12/th12_web/cpp/game/SceneCompositor.cpp',
 'docs/porting/TH14_BEHAVIOR_ACCEPTANCE_NOV13.md','docs/porting/TH14_BEHAVIOR_MATRIX_NOV13.md',
 'docs/porting/TH14_ALPHA_RANGE_INTEGRATION_NOV13.md','docs/porting/TH14_COMPOSITOR_FILTER_NOV13.md',
 'docs/porting/TH14_BACKGROUND_SAMPLER_DRAW_CONTRACT_NOV13.md','docs/porting/TH14_LOADING_BACKGROUND_UV_PHASE_NOV13.md',
 'docs/porting/th14-behavior-progress-nov13.json',
 'tools/th14-prepare-alpha-range-nov13.py','tools/th14-qualify-alpha-range-nov13.py','tools/th14-bind-alpha-range-providers-nov13.py',
 'tools/th14-run-alpha-range-current-nov13.mjs','tools/th14-build-behavior-browser-nov13.py',
 'tools/th14-prepare-current-normal-full-nov13.py','tools/th14-run-current-normal-full-nov13.mjs','tools/th14-audit-current-normal-full-nov13.py',
 'tools/th14-full-application-recording-platform-uniform2-nov13.mjs','tools/th14-prepare-behavior-matrix-nov13.py',
 'tools/th14-run-behavior-entry-nov13.mjs','tools/th14-run-behavior-matrix-nov13.py','tools/th14-qualify-behavior-matrix-nov13.py',
 'tools/th14-extra-unlock-save-nov13.cpp','tools/th14-prepare-extra-test-save-nov13.py',
 'tools/th14-run-extra-behavior-entry-nov13.mjs','tools/th14-run-extra-behavior-matrix-nov13.py',
 'tools/th14-full-application-gles-behavior-nov13.mjs','tools/th14-run-gpu-behavior-entry-nov13.mjs',
 'tools/th14-run-gpu-behavior-matrix-nov13.py','tools/th14-run-bomb-effect-tail-nov13.mjs',
 'tools/th14-background-sampler-pair-nov13.py','tools/th14-background-draw-contract-nov13.py',
 'tools/th14-background-draw-contract-nov13.cpp','tools/th14-build-background-draw-contract-nov13.py',
 'tools/th14-check-background-draw-contract-nov13.mjs','tools/th14-background-uv-phase-oracle-nov13.py',
 'tools/th14-publish-behavior-progress-nov13.py']
assert len(files)==len(set(files))and all(not n.startswith('artifacts/')for n in files)
snapshots={n:(R/n).read_bytes()for n in files};assert sum(map(len,snapshots.values()))<500000
def api(path,method=None,payload=None):
 cmd=[gh,'api',repo+'/'+path]
 if method:cmd+=['--method',method]
 if payload is not None:
  request=O/'request.json';request.write_text(json.dumps(payload),encoding='utf8');cmd+=['--input',str(request)]
 q=subprocess.run(cmd,cwd=R,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60)
 assert q.returncode==0,q.stderr.decode('utf8','replace')[:1500]
 return json.loads(q.stdout)
parent=api('git/ref/heads/main')['object']['sha'];assert parent=='371d3561c9d97842157a6b6a7b19b4fde31a86b5',parent
base_tree=api('git/commits/'+parent)['tree']['sha'];tree=[]
for n,b in snapshots.items():
 blob=api('git/blobs','POST',dict(content=base64.b64encode(b).decode(),encoding='base64'))['sha']
 assert blob==hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest(),n
 tree.append(dict(path=n,mode='100644',type='blob',sha=blob))
(O/'reviewed-plan.json').write_text(json.dumps(dict(parent=parent,baseTree=base_tree,files={n:dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())for n,b in snapshots.items()},onlyAllowlistedText=True,noRawAssetsSavesPixelsOrBinaries=True),indent=2)+'\n')
new_tree=api('git/trees','POST',dict(base_tree=base_tree,tree=tree))['sha']
message='Match TH14 compositor filtering and optimize alpha thresholds; verify behavior across loadouts\n\nRecord a122005-callback Normal run,30 menu/control cases and6 actual GPU loadouts under the user-requested behavioral acceptance scope. Keep full-mode, ordinary-save and browser delivery gaps open.\n\nCo-authored-by: Goan114 <Goan114@users.noreply.github.com>'
commit=api('git/commits','POST',dict(message=message,tree=new_tree,parents=[parent]))['sha']
assert api('git/ref/heads/main')['object']['sha']==parent,'Remote advanced; do not force'
for n,b in snapshots.items():assert(R/n).read_bytes()==b,n
api('git/refs/heads/main','PATCH',dict(sha=commit,force=False));assert api('git/ref/heads/main')['object']['sha']==commit
actual=api('git/commits/'+commit);assert actual['parents'][0]['sha']==parent and actual['tree']['sha']==new_tree
out=dict(commit=commit,parent=parent,tree=new_tree,files=len(files),bytes=sum(map(len,snapshots.values())),allBlobHashesVerified=True,refForce=False,sourceAndEvidencePublished=True,rawAssetsOrSavesOrPixelsUploaded=False,url='https://github.com/AdingApkgg/thp/commit/'+commit,deployed=False,completeGame=False)
(O/'published.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out),flush=True)
