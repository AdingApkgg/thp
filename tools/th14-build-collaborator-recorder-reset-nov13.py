"""Build the actual collaborator recorder before/after its shadowing fix."""
from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/collaborator-practice-review-nov13'
O=H/'recorder-reset';O.mkdir(exist_ok=False)
source=H/'overlay/runtimes/th12/th12_web/cpp/game'
original=(source/'ReplayRecorder.cpp').read_text();assert original.count('    practice={};practice_events={};')==1
provider=json.loads((R/'artifacts/th14/option-refresh-oracle-nov13/candidate-providers/build.json').read_bytes())
cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(cc)==provider['compilerSha256']
flags=[f for f in provider['flags']if not f.startswith('-I')]+['-I'+str(source),'-I'+str(R/'runtimes/th12/th12_web/cpp/game'),'-ffunction-sections','-fdata-sections']
fixture=R/'tools/th14-check-collaborator-recorder-reset-nov13.cpp';outputs={}
for mode in ['before','fixed']:
 directory=O/mode;directory.mkdir();body=original if mode=='before'else original.replace('    practice={};practice_events={};','    this->practice={};practice_events={};',1)
 cpp=directory/'ReplayRecorder.cpp';cpp.write_text(body,encoding='utf8',newline='\n')
 wasm=directory/'probe.wasm';cmd=[str(cc),*flags,'-mexec-model=reactor','-Wl,--no-entry','-Wl,--import-memory','-Wl,--export-memory','-Wl,--allow-undefined','-Wl,--initial-memory=67108864','-Wl,--max-memory=1073741824',str(fixture),str(cpp),'-o',str(wasm)]
 with(directory/'compile.log').open('wb')as f:q=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=90,env=dict(os.environ,TEMP=str(directory),TMP=str(directory),TMPDIR=str(directory)))
 assert q.returncode==0,(directory/'compile.log').read_text(errors='replace')[-2500:]
 outputs[mode]=dict(wasmSha256=sha(wasm),sourceSha256=sha(cpp))
j=dict(outputs=outputs,fixtureSha256=sha(fixture),compilerSha256=sha(cc),actualPatchedRecorder=True,gameAssetsLoaded=False,ordinaryProductionCoreChanged=False,completeGame=False)
(O/'build.json').write_text(json.dumps(j,indent=2)+'\n');print(json.dumps(j))
