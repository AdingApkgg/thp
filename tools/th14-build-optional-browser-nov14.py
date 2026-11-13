"""Build current optional Runtime from exact patch sources and compiler-checked reuse."""
from pathlib import Path
import json,hashlib,os,subprocess,sys,tempfile,importlib.util,shutil
from concurrent.futures import ThreadPoolExecutor,as_completed
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/beam-length-guard-nov14';P=R/'artifacts/th14/collaborator-review-cfb777c-nov13/activation-candidate';A=H/'optional-current-source';C=A/'core';common=A/'common';O=H/'optional-browser-build';O.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();j=json.loads((P/'build.json').read_bytes());plan=json.loads((H/'optional-dependency-plan.json').read_bytes());receipt=json.loads((H/'optional-current-source.json').read_bytes())
for n,h in receipt['files'].items():assert sha(A/n)==h,n
assert plan['units']==153 and plan['recompile']==25 and plan['reuse']==128
assert '-fno-access-control'not in j['flags'];sdk=R/'tools/emsdk';cc=sdk/'upstream/emscripten/emcc.py'
oldCore=R/'artifacts/th14/no-music-startup-nov13/site-patch/full-base';oldCommon=R/'artifacts/th14/collaborator-review-71bc5a0-nov13/common-source/common'
def remap(x):return x.replace(str(oldCore),str(C)).replace(str(oldCommon),str(common))
flags=[remap(x)for x in j['flags']];linkFlags=[remap(x)for x in j['linkFlags']];env=dict(os.environ,EMSDK=str(sdk),EMSDK_PYTHON=sys.executable,EM_CONFIG=str(sdk/'.emscripten'),EMCC_CORES='1')
changed=[str((A/n).resolve()).replace('\\','/').lower()for n in plan['sourceChanges']];objects={}
for name,digest in j['objects'].items():assert sha(P/name)==digest,name

def unit(row):
 name=row['object'];source=A/row['source'];target=O/name;target.parent.mkdir(parents=True,exist_ok=True);log=O/(Path(name).name+'.log')
 with tempfile.TemporaryDirectory(dir=O,prefix='unit-') as temp:
  unitEnv=dict(env,TEMP=temp,TMP=temp,TMPDIR=temp)
  if row['rebuild']:args=['-c',str(source),'-o',str(target)]
  else:args=['-M','-MF',str(O/(Path(name).name+'.d')),'-MT','checked',str(source)]
  cmd=[sys.executable,str(cc),*[f for f in flags if f!='--profiling-funcs'],*args]
  with log.open('wb') as out:p=subprocess.run(cmd,cwd=C/'runtimes/th12',env=unitEnv,stdout=out,stderr=subprocess.STDOUT,timeout=240)
  assert p.returncode==0,(name,log.read_text(errors='replace')[-3500:])
  if not row['rebuild']:
   deps=(O/(Path(name).name+'.d')).read_text().replace('\\\\','/').replace('\\','/').lower()
   assert not any(path in deps for path in changed),(name,'changed compiler dependency missed by conservative graph')
   os.link(P/name,target)
 return name,sha(target),row['rebuild']
count=rebuilt=reused=0
with ThreadPoolExecutor(max_workers=2) as pool:
 futures=[pool.submit(unit,row)for row in plan['rows']]
 for future in as_completed(futures):
  name,digest,fresh=future.result();objects[name]=digest;count+=1;rebuilt+=fresh;reused+=not fresh
  (O/'progress.json').write_text(json.dumps(dict(done=count,total=153,rebuilt=rebuilt,reusedCompilerChecked=reused))+'\n')
ordered={name:objects[name]for name in j['objects']};assert rebuilt==25 and reused==128
with tempfile.TemporaryDirectory(dir=O,prefix='link-') as temp:
 cmd=[*flags,*[str(O/n)for n in ordered],*linkFlags,'-o',str(O/'th14-sdl.mjs')];rsp=Path(temp)/'link.rsp';rsp.write_text('\n'.join(json.dumps(x.replace('\\','/'))for x in cmd),encoding='utf-8')
 with (O/'link.log').open('wb') as log:p=subprocess.run([sys.executable,str(cc),'@'+str(rsp)],cwd=C/'runtimes/th12',env=dict(env,TEMP=temp,TMP=temp,TMPDIR=temp),stdout=log,stderr=subprocess.STDOUT,timeout=300)
 assert p.returncode==0,(O/'link.log').read_text(errors='replace')[-3500:]
for n,record in j['runtimeFiles'].items():
 assert sha(P/n)==record['sha256'],n
 if n in ['th14-sdl.wasm','th14-sdl.mjs','shell.mjs']:continue
 source=C/'runtimes/th12/th12_web/sdl-runtime/eagler-host.mjs'if n=='eagler-host.mjs'else C/'runtimes/th12/portable/sdl'/n
 assert source.exists(),source
 shutil.copyfile(source,O/n)
spec=importlib.util.spec_from_file_location('builder',C/'tools/th14-build-gles.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder);digest=sha(O/'th14-sdl.wasm')
(O/'shell.mjs').write_text(builder.prepare_host_shell((C/'runtimes/th12/th12_web/sdl-runtime/shell.mjs').read_text(encoding='utf-8'),dict(version='1.00b-thp-'+digest[:12],completeGame=False,nativeEquivalent=False,sha256=digest)),encoding='utf-8',newline='\n')
for n,h in receipt['files'].items():assert sha(A/n)==h,n
for n,h in ordered.items():assert sha(O/n)==h,n
runtime={n:dict(bytes=(O/n).stat().st_size,sha256=sha(O/n))for n in j['runtimeFiles']}
result=dict(j,module=str(O/'th14-sdl.wasm'),flags=flags,linkFlags=linkFlags,sourceBindings={n:receipt['files']['core/'+n]for n in j['sourceBindings']},commonBindings={n:receipt['files']['common/'+n]for n in j['commonBindings']},objects=ordered,runtimeFiles=runtime,sha256=digest,loaderSha256=runtime['th14-sdl.mjs']['sha256'],unitsRecompiled=rebuilt,objectsVerifiedReused=reused,reusedDependenciesCompilerChecked=True,siteSource=receipt['site'],patchBase=receipt['base'],patchSha256=receipt['patchSha256'],normalAccessControl=True,browserAccepted=False,productionDeployed=False,completeGame=False,experimentalActivationHook=False)
(O/'build.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(wasm=digest,units=153,rebuilt=rebuilt,reused=reused,sourceBindings=387,commonBindings=24,runtimeFiles=len(runtime))))
