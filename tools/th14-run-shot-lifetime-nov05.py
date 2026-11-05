"""Collect bounded per-slot snapshots; require full selected-state transparency."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,time
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/shot-lifetime-nov05';SHA=lambda data:hashlib.sha256(data).hexdigest()

def main(case):
 assert shutil.disk_usage(R).free>100*1024**3
 old=R/'artifacts/th14/original-pair-audit-nov05/initialize-controls'/('stage3-player-late'if case=='late'else'baseline')
 report=json.loads((old/'result.json').read_bytes());source=(old/'driver.mjs').read_text();assert SHA((old/'driver.mjs').read_bytes())==report['diagnosticDriverSha256']=='ba00ca2726004956d7849204432999bcb3e543d8b1ecbb9ed6147bd1b24b7c81'
 if case!='off':assert json.loads((H/'off/result.json').read_bytes())['allSelectedStateBytesEqualPriorRun']
 out=H/case;assert not out.exists();out.mkdir()
 for name in ['startup-inputs.json','initialize-deltas.json']:(out/name).write_bytes((old/name).read_bytes())
 needle='function compare(index){\n const row=Array.from(new Uint32Array(c.memory.buffer,c.reference_data(),32));rows.push(...row);\n}'
 assert source.count(needle)==1
 source=source.replace(needle,'''const lifetimeSnapshots=[];
function compare(index){
 const row=Array.from(new Uint32Array(c.memory.buffer,c.reference_data(),32));rows.push(...row);
 if(c.shot_lifetime_meta(0)!==index+1)return;
 const meta=Array.from({length:6},(_,word)=>c.shot_lifetime_meta(word)>>>0);assert.equal(meta[3],96);assert.equal(meta[4],256);
 const values=new Uint32Array(c.memory.buffer,c.shot_lifetime_data(),96*256);
 assert.equal(Array.from({length:256},(_,slot)=>values[slot*96+1]).filter(Boolean).length,row[26]);
 const data=Buffer.from(values.buffer,values.byteOffset,values.byteLength),name='shot-lifetime-'+(index+1)+'.u32';
 write(resolve(out,name),data,{flag:'wx'});lifetimeSnapshots.push({callback:meta[0],stage:meta[1],stageFrame:meta[2],stride:96,slots:256,file:name,sha256:sha(data),bytes:data.length});
}
''')
 needle='if(auditFirst)assert.equal(c.rng_audit_install(auditFirst,auditLast),1);';assert source.count(needle)==1
 source=source.replace(needle,needle+'\nassert.equal(c.shot_lifetime_install('+str(int(case!='off'))+'),1);')
 source+="\nwrite(resolve(out,'shot-lifetime-index.json'),JSON.stringify({snapshots:lifetimeSnapshots,enabled:"+str(case!='off').lower()+",readOnly:true,originalPerSlotCompared:false,completeGame:false})+'\\n',{flag:'wx'});\n"
 driver=out/'driver.mjs';driver.write_text(source,encoding='utf8',newline='\n')
 subprocess.run(['C:/nvm4w/nodejs/node.exe','--check',str(driver)],check=True,capture_output=True,timeout=30)
 plan=json.loads((R/'artifacts/th14/supervisor-pass-rng-nov05/comparison-pump-enabled/plan.json').read_bytes());argv=list(plan['argv']);argv[2]=str(driver)
 argv[argv.index('--output')+1]=str(out/'model');argv[argv.index('--build')+1]=str(H/'build-retry1/observer-build.json')
 started=time.monotonic()
 with(out/'run.log').open('wb')as log:process=subprocess.run(argv,cwd=R,stdout=log,stderr=subprocess.STDOUT,timeout=240,creationflags=subprocess.CREATE_NO_WINDOW)
 result=dict(case=case,exitCode=process.returncode,elapsedSeconds=time.monotonic()-started,diagnosticDriverSha256=SHA(driver.read_bytes()),
  readOnlyProbe=True,originalPerSlotCompared=False,productionSourcesChanged=False,completeGame=False)
 if process.returncode==0:
  raw=(out/'model/diagnostic-state.u32').read_bytes();assert len(raw)==35000*128
  assert raw==(old/'model/diagnostic-state.u32').read_bytes()
  index=json.loads((out/'model/shot-lifetime-index.json').read_bytes());assert len(index['snapshots'])==(0 if case=='off'else 55)
  result.update(callbacks=35000,allSelectedStateBytesEqualPriorRun=True,selectedSha256=SHA(raw),snapshots=len(index['snapshots']),
   expectedPriorTrajectory='stage3-player-late'if case=='late'else'baseline')
 size=sum(path.stat().st_size for path in out.rglob('*')if path.is_file());assert size<50*1024**2
 result['outputBytes']=size;(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
 if process.returncode:raise SystemExit(process.returncode)

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',choices=['off','baseline','late'],required=True);main(p.parse_args().case)
