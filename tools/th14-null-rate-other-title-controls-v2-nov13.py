"""Compare optimized other-title objects through identical source paths."""
from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/player-initialization-oracle-nov13';O=H/'other-title-controls-v2';S=O/'runtimes/th12/th12_web/cpp/game';S.mkdir(parents=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();game=R/'runtimes/th12/th12_web/cpp/game'
for path in game.iterdir():
 if path.is_file()and path.suffix in ['.cpp','.hpp','.h','.inc']:os.link(path,S/path.name)
provider=json.loads((H/'candidate-providers/build.json').read_bytes());cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
assert sha(cc)==provider['compilerSha256']
for name in provider['sourceBindings']:
 if name.startswith('runtimes/th12/portable/'):
  target=O/name;target.parent.mkdir(parents=True,exist_ok=True);os.link(R/name,target)
base_flags=[f for f in provider['flags']if not f.startswith('-I')and not f.startswith('-DPORT_TITLE=')]
bindings={};results={}
for mode in ['baseline','candidate']:
 for name in ['Timer.hpp','PlayerFrame.cpp']:
  source=H/'baseline-source'/name if mode=='baseline'else game/name
  target=S/name;temp=S/(name+'.tmp');temp.write_bytes(source.read_bytes());os.replace(temp,target)
 for title in [12,13,16]:
  for name in ['PlayerFrame.cpp','AnmInterpreter.cpp']:
   obj=O/f'{mode}-{title}-{name}.o';cmd=[str(cc),*base_flags,f'-DPORT_TITLE={title}','-I'+str(S),'-c',str(S/name),'-o',str(obj)]
   with obj.with_suffix('.log').open('wb')as log:subprocess.run(cmd,cwd=R,env=dict(os.environ,TEMP=str(O),TMP=str(O),TMPDIR=str(O)),stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
   bindings[obj.relative_to(R).as_posix()]=sha(obj);results[mode,title,name]=sha(obj)
pairs=[dict(title=t,source=n,baselineSha256=results['baseline',t,n],candidateSha256=results['candidate',t,n],identical=results['baseline',t,n]==results['candidate',t,n])for t in [12,13,16]for n in ['PlayerFrame.cpp','AnmInterpreter.cpp']]
report=dict(passed=all(p['identical']for p in pairs),pairs=pairs,normalAccessControl=True,sameSourcePathsForBothPhases=True,compilerSha256=sha(cc),objectBindings=bindings,toolSha256=sha(Path(__file__)),completeGame=False)
(O/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=report['passed'],pairs=len(pairs))))
assert report['passed']
