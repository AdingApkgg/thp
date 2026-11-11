from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/ascii-queue-layout-nov12';load=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
layout=load(H/'candidate/checked.json');hud=load(H/'hud-candidate/checked.json');assert layout['cases']==6480 and layout['differentWords']==0 and hud['cases']==192 and hud['differentWords']==0
parent=load(R/'artifacts/th14/ascii-display-layout-nov12/current-provider-bindings.json');candidate=load(H/'candidate/build.json');assert candidate['freshlyCompiledGameUnits']==141
for row in candidate['objects']:assert sha(R/row['object'])==row['sha256']
names=['AsciiText.cpp','AsciiText.hpp','HudTh14Text.cpp'];game=R/'runtimes/th12/th12_web/cpp/game'
for name in names:assert (game/name).read_bytes()==(H/('before-'+name)).read_bytes()
protected=game/'ResourceCrypt.cpp';assert sha(protected)=='a291010053963e25dadef2be15ddb3c217110cd2377fc495402ef375150f8c45'
cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(cc)==parent['compilerSha256'];shared=H/'shared-v2';assert not shared.exists();shared.mkdir();pairs=[]
for title in [12,13,16]:
 for name in ['AsciiText.cpp','HudTh14Text.cpp']:
  outputs=[]
  for mode in ['before','candidate']:
   obj=shared/f'{title}-{mode}-{name}.o';vfs=shared/f'{title}-{mode}-{name}.vfs.json';vfs.write_text(json.dumps({'version':0,'use-external-names':False,'roots':[{'type':'file','name':str(game/n),'external-contents':str(H/(mode+'-'+n))} for n in names]}))
   flags=[f.replace('-DPORT_TITLE=14',f'-DPORT_TITLE={title}') for f in parent['flags']]
   with (shared/f'{title}-{mode}-{name}.log').open('wb') as log:subprocess.run([str(cc),*flags,'-ivfsoverlay',str(vfs),'-c',str(game/name),'-o',str(obj)],cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
   outputs.append(obj)
  assert outputs[0].read_bytes()==outputs[1].read_bytes(),(title,name)
  pairs.append(dict(title=title,source=name,beforeSha256=sha(outputs[0]),afterSha256=sha(outputs[1]),byteIdentical=True))
# Guard correction must preserve the TH14 object used by all comparisons.
obj=shared/'14-guarded-AsciiText.cpp.o'
with (shared/'14-guarded-AsciiText.cpp.log').open('wb') as log:subprocess.run([str(cc),*candidate['flags'],'-c',str(game/'AsciiText.cpp'),'-o',str(obj)],cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
assert obj.read_bytes()==(H/'candidate/AsciiText.cpp.o').read_bytes()
bindings={p.relative_to(R).as_posix():sha(p) for p in [Path(__file__),H/'native.json',H/'candidate/checked.json',H/'baseline/checked.json',H/'hud-sidebar-native-v2.json',H/'hud-awards-native-v2.json',H/'hud-candidate/checked.json',H/'hud-baseline/checked.json',H/'candidate/build.json',H/'hud-oracle-cache-correction.json']}
for p in R.joinpath('tools').glob('th14-*queue-layout*-nov12.*'):bindings[p.relative_to(R).as_posix()]=sha(p)
source_changes=[]
for name in names:
 source=game/name;temp=source.with_suffix('.queue-layout-pending'+source.suffix);temp.write_bytes((H/('candidate-'+name)).read_bytes());os.replace(temp,source);source_changes.append(dict(path=source.relative_to(R).as_posix(),beforeSha256=sha(H/('before-'+name)),afterSha256=sha(source)))
current_bindings=dict(candidate['sourceBindings']);current_bindings['runtimes/th12/th12_web/cpp/game/AsciiText.cpp']=sha(game/'AsciiText.cpp')
for path,digest in current_bindings.items():assert sha(R/path)==digest,path
report=dict(sourceAdopted=True,sharedGuardCorrectionTh14ObjectByteIdentical=True,currentSourceBindings=current_bindings,sourceChanges=source_changes,layoutCases=layout['cases'],layoutGlyphs=layout['glyphs'],layoutComparedWords=layout['comparedWords'],layoutDifferentWords=0,baselineSupportedLeftTopCases=1296,baselineUnsupportedAlignmentCases=5184,baselineFailedLeftTopCases=load(H/'baseline/checked.json')['failedCases'],hudCases=hud['cases'],hudGlyphs=hud['glyphs'],hudComparedWords=hud['comparedWords'],hudDifferentWords=0,hudBaselineFailedCases=load(H/'hud-baseline/checked.json')['failedCases'],freshlyCompiledNormalGameUnits=141,th14StyleLayoutChanged=True,allBrowserUnitsMustBeRebuilt=True,sharedTitleObjectPairs=pairs,protectedResourceCryptUnchanged=True,originalQueueAndTextTraversalExecuted=True,crtAtlasGeometryGpuDeclaredServices=True,stableDeviceSizeWithinQueueDrawDeclared=True,queueStoresLogicalCoordinatesUntilDraw=True,noPixels=True,newGameRuns=0,newGpuRuns=0,browserRuntimeUpdated=False,completeGame=False,bindings=bindings)
(H/'qualified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['bindings','sharedTitleObjectPairs','sourceChanges','currentSourceBindings']}))
