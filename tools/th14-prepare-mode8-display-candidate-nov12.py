"""Prepare an isolated TH14 mode8 display-space fix; keep production unchanged."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/mode8-display-space-nov12'
parser=argparse.ArgumentParser();parser.add_argument('--out-suffix',default='');args=parser.parse_args();assert args.out_suffix in ['', '-v2']
S=H/('candidate-source'+args.out_suffix);O=H/('candidate'+args.out_suffix);assert not S.exists() and not O.exists();S.mkdir();O.mkdir()
load=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
native=load(H/'native.json');core=load(R/'artifacts/th14/control-main-stop-nov12/current-core/build.json')
for name,digest in native['sourceBaseline'].items():assert sha(R/'runtimes/th12/th12_web/cpp/game'/name)==digest==sha(H/'baseline-source'/name)
game=R/'runtimes/th12/th12_web/cpp/game'
s=(game/'AnmProjection.hpp').read_text()
needle='#if PORT_TITLE == 14\nMatrix4 anm_legacy_world_matrix_th14'
assert s.count(needle)==1
s=s.replace(needle,'#if PORT_TITLE == 14\nMatrix4 anm_world_matrix_th14(AnmVm&,bool anchor_translation,const AnmRenderSpace&) noexcept;\nMatrix4 anm_legacy_world_matrix_th14')
(S/'AnmProjection.hpp').write_text(s,encoding='utf8',newline='\n')
s=(game/'AnmProjection.cpp').read_text()
needle='Matrix4 anm_world_matrix(AnmVm& vm,bool anchor_translation)noexcept{';assert s.count(needle)==1
s=s.replace(needle,'#if PORT_TITLE == 14\nMatrix4 anm_world_matrix_th14(AnmVm& vm,bool anchor_translation,const AnmRenderSpace& space)noexcept{\n#else\n'+needle+'\n#endif')
needle='if(((vm.flags2>>19)&7)==2){vm.transform_matrix.m[0]=float(vm.transform_matrix.m[0]*.5f);vm.transform_matrix.m[5]=float(vm.transform_matrix.m[5]*.5f);}'
assert s.count(needle)==1
s=s.replace(needle,'const u32 resolution=(vm.flags2>>19)&7;\n        if(resolution==1||resolution==2){\n            const float factor=resolution==2?float(space.scale*.5f):space.scale;\n            vm.transform_matrix.m[0]=float(vm.transform_matrix.m[0]*factor);vm.transform_matrix.m[5]=float(vm.transform_matrix.m[5]*factor);\n        }')
needle='float(local_y-float(float(vm.pivot.y*vm.scale.y)*vm.extra_scale.y)),0});';assert s.count(needle)==1
s=s.replace(needle,'float(local_y-float(float(vm.pivot.y*vm.scale.y)*vm.extra_scale.y)),0},space);')
needle='bool anm_projected_quad(AnmVm& vm,';assert s.count(needle)==1
s=s.replace(needle,'#if PORT_TITLE == 14\nMatrix4 anm_world_matrix(AnmVm& vm,bool anchor_translation)noexcept{return anm_world_matrix_th14(vm,anchor_translation,{});}\n#endif\n'+needle)
(S/'AnmProjection.cpp').write_text(s,encoding='utf8',newline='\n')
s=(game/'AnmRenderer.cpp').read_text()
needle='flush();const auto world=anm_world_matrix(vm,kPortTitle!=13&&kPortTitle!=14);material(vm);'
assert s.count(needle)==1
s=s.replace(needle,'flush();\n#if PORT_TITLE == 14\n        const float display_scale=float(render_width)/640.f;\n        // Native446905/446910 and446c8f/446cb1 use distinct origins.\n        const AnmRenderSpace space{display_scale,\n            {float(i32(render_width)/2),float((i32(render_height)-448)/2)},\n            {float(i32(render_width)/2),float(i32(float(display_scale*16.f)))}};\n        const auto world=anm_world_matrix_th14(vm,false,space);\n#else\n        const auto world=anm_world_matrix(vm,kPortTitle!=13&&kPortTitle!=14);\n#endif\n        material(vm);')
(S/'AnmRenderer.cpp').write_text(s,encoding='utf8',newline='\n')
vfs=H/('candidate-vfs'+args.out_suffix+'.json')
vfs.write_text(json.dumps({'version':0,'case-sensitive':False,'roots':[{'type':'file','name':(game/name).as_posix(),'external-contents':(S/name).as_posix(),'use-external-name':False} for name in native['sourceBaseline']]},indent=2)+'\n')
cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
assert sha(cc)==core['compilerSha256']
for p,d in core['sourceBindings'].items():assert sha(R/p)==d,p
for row in core['currentProviders']:assert sha(Path(row['object']))==row['objectSha256']
flags=core['flags']+['-ivfsoverlay',str(vfs)]
objects=[];changed=[];commands=[]
env={**os.environ,'TEMP':str(O),'TMP':str(O),'TMPDIR':str(O)}
for row in core['currentProviders']:
 p=R/row['source']
 if p.name in ['AnmProjection.cpp','AnmRenderer.cpp']:
  obj=O/(p.name+'.o');cmd=[str(cc),*flags,'-c',str(p),'-o',str(obj)];commands.append(cmd)
  with (O/(p.name+'.log')).open('wb') as f:subprocess.run(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=240,env=env)
  objects.append(str(obj));changed.append(dict(source=p.relative_to(R).as_posix(),candidateSourceSha256=sha(S/p.name),objectSha256=sha(obj)))
 else:objects.append(row['object'])
fixture=R/'tools/th14-mode8-display-component-nov12.cpp'
cmd=[str(cc),*flags,'-DTH14_MODE8_SPACE_CANDIDATE=1','-mexec-model=reactor','-Wl,--no-entry','-Wl,--import-memory','-Wl,--export-memory','-Wl,--allow-undefined',
 '-Wl,--initial-memory=67108864','-Wl,--max-memory=1073741824','-Wl,-z,stack-size=1048576',str(fixture),*objects,'-o',str(O/'probe.wasm')];commands.append(cmd)
with (O/'link.log').open('wb') as f:subprocess.run(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=240,env=env)
(O/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
meta=dict(wasmSha256=sha(O/'probe.wasm'),compilerSha256=sha(cc),flags=flags,objects=objects,changedProviders=changed,
 coreBuildSha256=sha(R/'artifacts/th14/control-main-stop-nov12/current-core/build.json'),normalProviderAccess=True,
 sourceOverrides={str((game/p.name).relative_to(R)).replace('\\','/'):dict(path=p.relative_to(R).as_posix(),sha256=sha(p)) for p in S.iterdir()},
 fixturePath=fixture.relative_to(R).as_posix(),fixtureSha256=sha(fixture),fixtureNormalAccess=True,
 productionChanged=False,completeGame=False,toolSha256=sha(Path(__file__)))
(O/'build.json').write_text(json.dumps(meta,indent=2)+'\n')
print(json.dumps(dict(compiled=True,wasmSha256=meta['wasmSha256'],changedProviders=len(changed),reusedProviders=len(objects)-len(changed),productionChanged=False)))
