import createModule from './th11.mjs';
import {createTh14SaveDelta,th14IdbfsDeltaAdapter} from './delta.mjs';
const $=s=>document.querySelector(s),sha=async b=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',b)),n=>n.toString(16).padStart(2,'0')).join('');
let used=false;
$('#run').addEventListener('click',async()=>{
 if(used)return;used=true;$('#run').disabled=true;
 const report={schema:'th14-save-delta-browser-v1',diagnosticOnly:true,productionGameChanged:false,actualIndexedDb:true,actualEmscriptenFs:true,actualIdbfs:true,actualGameFrames:0,audioPlayed:false,gpuDraws:0,cases:[],error:null};
 const check=(ok,message)=>{if(!ok)throw Error(message);};
 const test=(name,details={})=>{report.cases.push({name,passed:true,...details});$('#result').textContent=JSON.stringify(report,null,2);};
 const sync=(m,populate)=>new Promise((yes,no)=>m.FS.syncfs(populate,e=>e?no(e):yes()));
 const root='/savesth14',path=name=>root+'/'+name;
 const write=(m,name,bytes)=>m.FS.writeFile(path(name),new Uint8Array(bytes));
 try{
  $('#status').textContent='初始化两个真实 SDL 文件系统（不运行游戏或音频）';
  const binary=await (await fetch('./th11.wasm')).arrayBuffer();report.wasmSha256=await sha(binary);check(report.wasmSha256==='7e42a509065676ece981f2e8e5e7ce9a86d2960d02149398b1c0c0316c15f088','Release WASM identity');
  const modules=[];report.database='th14-delta-qa-'+crypto.randomUUID();
  for(let i=0;i<2;++i){
   const m=await createModule({wasmBinary:new Uint8Array(binary),canvas:document.querySelectorAll('canvas')[i],noInitialRun:true,print:()=>{},printErr:line=>console.error(line)});
   const original=m.IDBFS.getDB;
   // The real IDBFS implementation is unchanged; isolate its database name.
   m.IDBFS.getDB=(name,callback)=>{check(name===root,'Only owned test mount');return original(report.database,callback);};
   m.FS.mkdirTree(root);m.FS.mount(m.IDBFS,{},root);await sync(m,true);m.FS.mkdirTree(path('replay'));modules.push(m);
  }
  const [a,b]=modules;
  const db=await new Promise((yes,no)=>a.IDBFS.getDB(root,(e,d)=>e?no(e):yes(d)));
  const remote=name=>new Promise((yes,no)=>{const tx=db.transaction(['FILE_DATA'],'readonly'),r=tx.objectStore('FILE_DATA').get(path(name));r.onsuccess=()=>yes(r.result);r.onerror=()=>no(r.error);});
  const bytes=async name=>{const e=await remote(name);return e?Array.from(e.contents??[]):null;};
  write(a,'scoreth14.dat',[1,2,3]);write(a,'replay/th14_01.rpy',[11]);await sync(a,false);await sync(b,true);
  write(b,'replay/th14_ud0000.rpy',[22]);await sync(b,false);check((await bytes('replay/th14_ud0000.rpy'))?.[0]===22,'Control import persisted');
  await sync(a,false);check(await bytes('replay/th14_ud0000.rpy')===null,'Unchanged original full-tree writer must reproduce stale deletion');
  test('unchanged-idbfs-stale-writer-negative-control',{newReplayDeleted:true});
  const da=th14IdbfsDeltaAdapter(a);await da.loaded();
  await sync(b,false);const dbStore=th14IdbfsDeltaAdapter(b);await dbStore.loaded();
  write(a,'scoreth14.dat',[4,5,6]);await da.flush();
  check(JSON.stringify(await bytes('scoreth14.dat'))==='[4,5,6]'&&(await bytes('replay/th14_ud0000.rpy'))?.[0]===22,'Old local tree must preserve imported replay');
  test('old-writer-score-change-preserves-new-replay');
  write(b,'replay/th14_ud0001.rpy',[33]);await dbStore.flush();
  check(JSON.stringify(await bytes('scoreth14.dat'))==='[4,5,6]'&&(await bytes('replay/th14_ud0001.rpy'))?.[0]===33,'Unchanged stale score must not overwrite remote');
  test('unchanged-stale-score-not-rewritten');
  write(a,'replay/th14_ud0002.rpy',[44]);await da.flush();
  write(b,'replay/th14_00.rpy',[55]);write(b,'replay/th14_ud0002.rpy',[66]);
  let conflict=false;try{await dbStore.flush();}catch(e){conflict=/另一个窗口/.test(String(e));}
  check(conflict&&(await bytes('replay/th14_ud0002.rpy'))?.[0]===44&&await bytes('replay/th14_00.rpy')===null,'Same-slot conflict must roll back every queued write');
  test('same-slot-conflict-atomic-rollback');
  b.FS.unlink(path('replay/th14_00.rpy'));b.FS.unlink(path('replay/th14_ud0002.rpy'));
  a.FS.unlink(path('replay/th14_01.rpy'));await da.flush();write(b,'replay/th14_ud0003.rpy',[77]);await dbStore.flush();
  check(await bytes('replay/th14_01.rpy')===null&&(await bytes('replay/th14_ud0003.rpy'))?.[0]===77,'Stale unchanged file must not resurrect a deletion');
  test('explicit-delete-preserved-by-stale-writer');
  const oldTime=a.FS.stat(path('scoreth14.dat')).mtime;write(a,'scoreth14.dat',[8,9]);a.FS.utime(path('scoreth14.dat'),oldTime,oldTime);await da.flush();
  check(JSON.stringify(await bytes('scoreth14.dat'))==='[8,9]','Same timestamp with different bytes must persist');test('same-timestamp-different-bytes');
  await sync(b,true);const refreshedB=th14IdbfsDeltaAdapter(b);await refreshedB.loaded();write(b,'replay/th14_ud0002.rpy',[88]);await refreshedB.flush();
  a.FS.unlink(path('replay/th14_ud0002.rpy'));let deleteConflict=false;try{await da.flush();}catch(e){deleteConflict=/未执行删除/.test(String(e));}
  check(deleteConflict&&(await bytes('replay/th14_ud0002.rpy'))?.[0]===88,'Stale deletion must not erase a newer file');test('stale-delete-conflict-retains-remote');
  // Refresh the test filesystem after the intentional conflict; do not change game state.
  await sync(a,true);const retry=th14IdbfsDeltaAdapter(a);await retry.loaded();
  const nativeTransaction=db.transaction.bind(db);let inject=true;
  Object.defineProperty(db,'transaction',{configurable:true,value(...args){const tx=nativeTransaction(...args);if(inject&&args[1]==='readwrite'){inject=false;queueMicrotask(()=>tx.abort());}return tx;}});
  write(a,'replay/th14_ud0004.rpy',[99]);let aborted=false;try{await retry.flush();}catch{aborted=true;}
  check(aborted&&await bytes('replay/th14_ud0004.rpy')===null,'Injected real transaction abort must persist nothing');
  delete db.transaction;await retry.flush();check((await bytes('replay/th14_ud0004.rpy'))?.[0]===99,'Failed flush must retain baseline for retry');
  test('injected-real-transaction-abort-then-retry',{injectedAbort:true,actualQuotaError:false});
  let begun;const begunPromise=new Promise(yes=>begun=yes);
  Object.defineProperty(db,'transaction',{configurable:true,value(...args){const tx=nativeTransaction(...args);if(args[1]==='readwrite')begun();return tx;}});
  write(a,'scoreth14.dat',[100]);const first=retry.flush();await begunPromise;write(a,'scoreth14.dat',[101]);const second=retry.flush();await first;await second;delete db.transaction;
  check((await bytes('scoreth14.dat'))?.[0]===101,'Writes during an in-flight flush must remain for the next flush');test('serialized-flush-retains-midflight-local-change');
  report.passed=true;report.executedCases=report.cases.length;report.privateTestDatabaseRetained=true;
 }catch(error){report.passed=false;report.error=String(error?.stack??error);}
 $('#status').textContent=report.passed?'真实 IndexedDB / IDBFS 控制全部通过':'有失败，完整结果已保留';$('#result').textContent=JSON.stringify(report,null,2);
 const result=await fetch('./capture/report',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(report)});check(result.ok,'Save complete report');
});
