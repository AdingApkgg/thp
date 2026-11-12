from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/loading-control4-nov13';O=H/'rate-diagnostic-v2';O.mkdir()
load=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
base=load(H/'component/build.json');provider=load(H/'provider/build.json')
for n,d in {**base['sourceBindings'],**base['observerBindings']}.items():assert sha(R/n)==d,n
for row in provider['currentProviders']:assert sha(R/row['object'])==row['objectSha256']
source=(H/'component/fixture.cpp').read_text()+'''
std::vector<u32> diagnostic_rates;
API(rate_bindings) u32 rate_bindings(){
 diagnostic_rates.clear();auto& a=*owner;
 for(auto* p:seen)if(p->id&&a.find(p->id)==p){
  diagnostic_rates.insert(diagnostic_rates.end(),{p->id,u32(p->script_index),u32(uintptr_t(&a.rate)),u32(uintptr_t(p->timer.rate)),
   u32(uintptr_t(p->alpha_interpolation.timer.rate)),u32(p->alpha_interpolation.duration),u32(p->alpha_interpolation.timer.current),float_bits(p->alpha_interpolation.timer.fractional)});
 }
 return u32(diagnostic_rates.size());
}
API(rate_data) const u32* rate_data(){return diagnostic_rates.data();}
'''
fixture=O/'fixture.cpp';fixture.write_text(source)
cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(cc)==provider['compilerSha256']
command=[str(cc),*provider['flags'],'-mexec-model=reactor','-Wl,--no-entry','-Wl,--import-memory','-Wl,--export-memory','-Wl,--allow-undefined','-Wl,--initial-memory=67108864','-Wl,--max-memory=1073741824','-Wl,-z,stack-size=1048576',str(fixture),*[row['object']for row in provider['currentProviders']],'-o',str(O/'probe.wasm')]
with(O/'build.log').open('wb')as log:subprocess.run(command,cwd=R,stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,TMP=str(O),TEMP=str(O),TMPDIR=str(O)),check=True,timeout=120)
bindings=dict(base['observerBindings']);bindings[fixture.relative_to(R).as_posix()]=sha(fixture)
j={**base,'observerBindings':bindings,'wasmSha256':sha(O/'probe.wasm'),'command':command,'readOnlyRatePointerObservation':True,'dereferenceObservedPointers':False}
(O/'build.json').write_text(json.dumps(j,indent=2)+'\n');print(json.dumps({'wasmSha256':j['wasmSha256']}))
runner=(R/'tools/th14-run-loading-control4-nov13.mjs').read_text();runner=runner.replace('const cases=[];let totalWords=0,totalFrames=0;','const rates=[];const cases=[];let totalWords=0,totalFrames=0;')
needle='  const a=Array.from(new Uint32Array(memory.buffer,c.data(),length));'
assert runner.count(needle)==1
runner=runner.replace(needle,'''  if(frame<=2){const n=c.rate_bindings();rates.push({name:record.name,frame,stride:8,words:Array.from(new Uint32Array(memory.buffer,c.rate_data(),n))});}
'''+needle)
needle='const report={passed:';assert runner.count(needle)==1;runner=runner.replace(needle,"writeFileSync(resolve(output,'rate-bindings.json'),JSON.stringify(rates,null,2)+'\\n');\n"+needle)
(R/'tools/th14-run-loading-control4-rates-nov13.mjs').write_text(runner,newline='\n')
