from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/ascii-display-layout-nov12';load=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=load(H/'baseline/checked.json');after=load(H/'candidate/checked.json');assert before['failedCases']==480 and after['failedCases']==0 and after['comparedWords']==71280
source=R/'runtimes/th12/th12_web/cpp/game/AsciiText.cpp';assert source.read_bytes()==(H/'before.cpp').read_bytes()
protected=R/'runtimes/th12/th12_web/cpp/game/ResourceCrypt.cpp';assert sha(protected)=='a291010053963e25dadef2be15ddb3c217110cd2377fc495402ef375150f8c45'
core=load(R/'artifacts/th14/mode8-display-space-nov12/current-core/build.json');cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(cc)==core['compilerSha256']
shared=H/'shared-v2';assert not shared.exists();shared.mkdir();pairs=[]
for title in [12,13,16]:
 flags=[x.replace('-DPORT_TITLE=14',f'-DPORT_TITLE={title}') for x in core['flags']];objects=[]
 for mode in ['before','candidate']:
  vfs=shared/f'{title}-{mode}.vfs.json';vfs.write_text(json.dumps({'version':0,'use-external-names':False,'roots':[{'type':'file','name':str(source),'external-contents':str(H/(mode+'.cpp'))}]}));obj=shared/f'{title}-{mode}.o'
  with (shared/f'{title}-{mode}.log').open('wb') as log:subprocess.run([str(cc),*flags,'-ivfsoverlay',str(vfs),'-c',str(source),'-o',str(obj)],cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
  objects.append(obj)
 assert objects[0].read_bytes()==objects[1].read_bytes(),title
 pairs.append(dict(title=title,beforeSha256=sha(objects[0]),afterSha256=sha(objects[1]),byteIdentical=True))
bindings={p.relative_to(R).as_posix():sha(p) for p in [Path(__file__),R/'tools/th14-ascii-display-layout-native-nov12.py',R/'tools/th14-build-ascii-display-layout-nov12.py',R/'tools/th14-ascii-display-layout-component-nov12.cpp',R/'tools/th14-check-ascii-display-layout-nov12.mjs',H/'native.json',H/'baseline/checked.json',H/'candidate/checked.json',H/'before.cpp',H/'candidate.cpp']}
# The non-TH14 constexpr branch needed a visible name even when discarded.
vfs=H/'candidate-vfs.json';obj=shared/'14-candidate.o'
with (shared/'14-candidate.log').open('wb') as log:subprocess.run([str(cc),*core['flags'],'-ivfsoverlay',str(vfs),'-c',str(source),'-o',str(obj)],cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
assert obj.read_bytes()==(H/'candidate/AsciiText.cpp.o').read_bytes()
temp=source.with_suffix('.layout-pending.cpp');temp.write_bytes((H/'candidate.cpp').read_bytes());os.replace(temp,source)
report=dict(sourceBeforeSha256=sha(H/'before.cpp'),sourceAfterSha256=sha(source),sourceAdopted=True,cases=after['cases'],glyphs=after['glyphs'],comparedWords=after['comparedWords'],baselineFailedCases=before['failedCases'],baselineDifferentWords=before['differentWords'],candidateFailedCases=0,sharedTitleObjectPairs=pairs,protectedResourceCryptUnchanged=True,normalProviderAccess=True,original40bf20Executed=True,rendererGeometryAndGpuDeclaredServices=True,syntheticAtlas=True,leftTopAlignmentOnly=True,noPixels=True,newGameRuns=0,newGpuRuns=0,browserRuntimeUpdated=False,completeGame=False,bindings=bindings)
(H/'qualified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['bindings','sharedTitleObjectPairs']}))
