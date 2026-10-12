// Read-only original-demo probe: selective cache bypass localizes a regression.
import {readFileSync,writeFileSync} from 'node:fs';
import {WASI} from 'node:wasi';
const bytes=readFileSync('artifacts/th14/startup-session/startup.wasm'),target=JSON.parse(readFileSync('runtimes/th14/target.json','utf8')),dat=readFileSync(target.dataArchives['th14.dat'].path),rows=[];
for(const mask of [0,1,2,4,8,15]){
 const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports,p=c.allocate(dat.length);new Uint8Array(c.memory.buffer,p,dat.length).set(dat);if(!c.open_archive(p,dat.length)||!c.begin_demo(1))throw Error('resource load');c.template_disable(mask);
 let checkpoints=[];for(let frame=1;frame<=3400;++frame){if(!c.tick(0)||!c.draw())throw Error('update');if(frame>=3280&&frame<=3286)checkpoints.push({frame,gameplaySeed:c.deferred_state(2),gameplayCalls:c.deferred_state(3),visualSeed:c.replay_observation(13),visualCalls:c.replay_observation(14)});}
 rows.push({mask,checkpoints});console.log(JSON.stringify(rows.at(-1)));
}
writeFileSync('artifacts/th14/anm-template-diagnostic-oct11.json',JSON.stringify(rows,null,2)+'\n');
