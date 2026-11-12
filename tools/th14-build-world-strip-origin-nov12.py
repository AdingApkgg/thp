"""Build a single-unit origin fix and an unchanged-code negative control."""
from pathlib import Path
import difflib,hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/world-strip-origin-nov12';S=H/'source';S.mkdir(exist_ok=False)
base_path=R/'artifacts/th14/display-consumers-nov12/current-provider-bindings.json';base=json.loads(base_path.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,digest in base['sourceBindings'].items():
    assert sha(R/name)==digest,name;p=S/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((R/name).read_bytes())
name='runtimes/th12/th12_web/cpp/game/AnmRenderer.cpp';p=S/name;before=p.read_text(encoding='utf8')
old='if((vm.flags2&0x60000)&&!vm.parent)world.m[12]=float(world.m[12]+320.f);'
new='''// Retail4785ed reads the play origin; resource-present Begin sets it to width/2.
    if((vm.flags2&0x60000)&&!vm.parent)world.m[12]=float(world.m[12]+float(i32(render_width)/2));'''
assert before.count(old)==1;after=before.replace(old,new);p.write_text(after,encoding='utf8',newline='')
(H/'reviewed-source.diff').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile=name,tofile=name)),encoding='utf8')
O=H/'component';O.mkdir(exist_ok=False);cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(cc)==base['compilerSha256']
flags=[('-I'+str(S/Path(v[2:]).relative_to(R))) if v.startswith('-I') and Path(v[2:]).is_relative_to(R/'runtimes/th12') else v for v in base['flags']]
env={**os.environ,'TEMP':str(O),'TMP':str(O),'TMPDIR':str(O)};obj=O/'AnmRenderer.cpp.o'
with (O/'compile.log').open('wb') as log:subprocess.run([str(cc),*flags,'-c',str(p),'-o',str(obj)],cwd=R,stdout=log,stderr=subprocess.STDOUT,env=env,check=True,timeout=120)
providers=[];baseline=base['currentProviders']
for row in baseline:
    assert sha(R/row['object'])==row['objectSha256']
    providers.append(dict(source=name,sourceSha256=sha(p),object=obj.relative_to(R).as_posix(),objectSha256=sha(obj)) if row['source']==name else row)
fixture=R/'tools/th14-world-strip-origin-component-nov12.cpp'
for label,rows in [('candidate',providers),('baseline',baseline)]:
    with (O/(label+'.link.log')).open('wb') as log:
        subprocess.run([str(cc),*flags,'-mexec-model=reactor','-Wl,--no-entry','-Wl,--import-memory','-Wl,--export-memory','-Wl,--allow-undefined','-Wl,--initial-memory=67108864','-Wl,--max-memory=1073741824','-Wl,-z,stack-size=1048576',str(fixture),*[str(R/x['object']) for x in rows],'-o',str(O/(label+'.wasm'))],cwd=R,stdout=log,stderr=subprocess.STDOUT,env=env,check=True,timeout=120)
report=dict(sourceRoot=str(S),sourceBindings={n:sha(S/n) for n in base['sourceBindings']},currentProviders=providers,baselineProviders=baseline,flags=flags,
    changes=[dict(path=name,beforeSha256=sha(R/name),afterSha256=sha(p))],compilerSha256=sha(cc),fixtureSha256=sha(fixture),baseManifestSha256=sha(base_path),
    normalAccess=True,freshlyCompiledUnits=1,unchangedVerifiedProviders=140,modules={label:sha(O/(label+'.wasm')) for label in ('candidate','baseline')},
    canonicalSourceChanged=False,completeGame=False)
(O/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(freshlyCompiledUnits=1,unchangedVerifiedProviders=140,normalAccess=True,modules=report['modules'])))
