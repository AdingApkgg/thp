"""Require byte-identical shared renderer/projection objects for TH13/TH16."""
from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/mode8-display-space-nov12'
O=H/'other-titles';assert not O.exists();O.mkdir()
load=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
core=load(R/'artifacts/th14/control-main-stop-nov12/current-core/build.json')
cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(cc)==core['compilerSha256']
rows=[]
for title in [13,16]:
 for name in ['AnmProjection.cpp','AnmRenderer.cpp']:
  source=R/'runtimes/th12/th12_web/cpp/game'/name
  flags=[x.replace('-DPORT_TITLE=14','-DPORT_TITLE='+str(title)) for x in core['flags']]
  result={}
  for mode in ['baseline','candidate']:
   out=O/(f'th{title}-'+mode+'-'+name+'.o')
   cmd=[str(cc),*flags,*(['-ivfsoverlay',str(H/'candidate-vfs-v2.json')] if mode=='candidate' else []),'-c',str(source),'-o',str(out)]
   with (out.with_suffix('.log')).open('wb') as f:subprocess.run(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=180,env={**os.environ,'TEMP':str(O),'TMP':str(O),'TMPDIR':str(O)})
   result[mode]=sha(out)
  rows.append(dict(title=title,source=name,objectSha256=result,byteIdentical=result['baseline']==result['candidate']))
report=dict(rows=rows,allFourObjectsByteIdentical=all(x['byteIdentical'] for x in rows),
 actualCompilerInvocations=8,rootProductionChanged=False,otherGamesRuntimeNotAccepted=True,completeGame=False)
(O/'qualified.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report));assert report['allFourObjectsByteIdentical']
