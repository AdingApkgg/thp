import {spawn} from 'node:child_process';
import {existsSync,mkdirSync,mkdtempSync,readFileSync,writeFileSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {decodeScoreFile,scoreChunkTag} from '../shared/th06nc/score-file.mjs';
import {decodeReplayFile} from '../shared/th06nc/replay-file.mjs';
import {highScoreFields} from '../shared/th06nc/score-tables.mjs';

const extra=false,suffix='achievements',sha=b=>createHash('sha256').update(b).digest('hex'),sources=[...readdirSync('shared/th06nc').filter(n=>n.endsWith('.mjs')).map(n=>'shared/th06nc/'+n),...['game.mjs','game-assets.mjs','game-renderer.mjs','game-audio.mjs','game-save.mjs','game-achievements.mjs'].map(n=>'runtimes/th06nc/'+n)],hashes=()=>Object.fromEntries(sources.map(p=>[p,sha(readFileSync(p))])),sourceSha256=hashes(),home=resolve('artifacts/th06nc/'+suffix+'-browser');mkdirSync(home,{recursive:true});
const chrome=['C:/Program Files/Google/Chrome/Application/chrome.exe','C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'].find(existsSync),child=spawn(chrome,['--headless=new','--no-sandbox','--enable-unsafe-swiftshader','--mute-audio','--no-first-run','--remote-debugging-port=9499','--user-data-dir='+mkdtempSync(resolve('tools/tmp/th06nc-ending-')),'about:blank'],{stdio:'ignore'}),sleep=ms=>new Promise(r=>setTimeout(r,ms));let socket;
try{
 let tab;for(let n=0;n<100;n++){try{tab=(await(await fetch('http://127.0.0.1:9499/json/list')).json()).find(t=>t.type==='page');if(tab)break;}catch{}await sleep(100);}assert.ok(tab);socket=new WebSocket(tab.webSocketDebuggerUrl);await new Promise((ok,bad)=>{socket.onopen=ok;socket.onerror=bad;});let serial=0;const requests=new Map(),errors=[];socket.onmessage=e=>{const m=JSON.parse(e.data);if(m.id){const p=requests.get(m.id);requests.delete(m.id);m.error?p.reject(Error(m.error.message)):p.resolve(m.result);}else if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails.exception?.description??m.params.exceptionDetails.text);};const send=(method,params={})=>new Promise((resolve,reject)=>{const id=++serial;requests.set(id,{resolve,reject});socket.send(JSON.stringify({id,method,params}));}),evaluate=async expression=>{const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(r.exceptionDetails.exception?.description??r.exceptionDetails.text);return r.result.value;},wait=async expression=>{for(let n=0;n<900;n++){if(errors.length)throw Error(errors.join('\n'));if(await evaluate(expression))return;await sleep(100);}throw Error('Readiness timeout '+expression);},picture=async name=>{const p=await send('Page.captureScreenshot',{format:'png'});writeFileSync(resolve(home,name+'.png'),Buffer.from(p.data,'base64'));};await send('Runtime.enable');await send('Page.enable');await send('Page.addScriptToEvaluateOnNewDocument',{source:'Date.now=()=>9909;'});await send('Page.navigate',{url:'http://127.0.0.1:8268/runtimes/th06nc/game.html'});await wait('globalThis.th06ncGame?.report().phase==="title"');
 await evaluate('th06ncGame.setManual(true)');await evaluate('th06ncGame.advance(360,0)');if((await evaluate('th06ncGame.report().titleState'))===2){await evaluate('th06ncGame.advance(1,256)');await evaluate('th06ncGame.advance(90,0)');}const codes={z:['z','KeyZ',90],x:['x','KeyX',88],up:['ArrowUp','ArrowUp',38],down:['ArrowDown','ArrowDown',40],left:['ArrowLeft','ArrowLeft',37],right:['ArrowRight','ArrowRight',39]},tap=async(key,frames=90)=>{const [value,code,number]=codes[key],event={key:value,code,windowsVirtualKeyCode:number,nativeVirtualKeyCode:number};await send('Input.dispatchKeyEvent',{type:'keyDown',...event});await evaluate('th06ncGame.advance(1)');await send('Input.dispatchKeyEvent',{type:'keyUp',...event});const state=await evaluate('th06ncGame.advance('+frames+',0)');assert.equal(state.error,null,JSON.stringify(state));assert.equal(state.glError,0);return state;},evidence=[];

 const result=await evaluate(`(async()=>{
 const {GameSave}=await import('./game-save.mjs');
 const db='th06nc-achievement-check',s=new GameSave({databaseName:db});await s.open();
 const a=s.achievements,initial=a.report(),score=s.scoreFile(),config=[...s.configBytes];
 a.award('Achievement02');a.award('Achievement02');const staged=a.report();
 const observer=new GameSave({databaseName:db});await observer.open();const beforeCommit=observer.achievements.report();
 await a.commit();const committed=a.report();
 observer.achievements.award('Achievement22');await observer.achievements.commit();
 a.award('Achievement20');await a.commit();
 const union=new GameSave({databaseName:db});await union.open();const combined=union.achievements.report();
 a.award('Achievement03');const complete=a.complete.bind(a);a.complete=tx=>{const promise=complete(tx);tx.abort();return promise;};let failed=false;
 try{await a.commit();}catch{failed=true;}const aborted=a.report();a.complete=complete;
 const probe=new GameSave({databaseName:db});await probe.open();const onDiskAfterAbort=probe.achievements.report();
 await a.commit();const recovered=a.report();
 a.award('Achievement04');const first=a.commit();a.award('Achievement05');const second=a.commit();await Promise.all([first,second]);
 let invalid=false;try{a.award('Achievement25');}catch{invalid=true;}
 const r=new GameSave({databaseName:db});await r.open();const reopened=r.achievements.report(),unchanged=JSON.stringify(config)===JSON.stringify([...r.configBytes])&&JSON.stringify(score)===JSON.stringify(r.scoreFile());
 for(const save of [s,observer,union,probe,r])save.db.close();
 return {initial,staged,beforeCommit,committed,combined,failed,aborted,onDiskAfterAbort,recovered,reopened,invalid,unchanged};
 })()`);
 assert.deepEqual(result.initial.unlocked,[]);assert.deepEqual(result.staged.pending,['Achievement02']);assert.deepEqual(result.beforeCommit.unlocked,[]);
 assert.deepEqual(result.committed.unlocked,['Achievement02']);assert.deepEqual(result.combined.unlocked,['Achievement02','Achievement20','Achievement22']);
 assert.equal(result.failed,true);assert.deepEqual(result.aborted.pending,['Achievement03']);assert.ok(result.aborted.error);assert.ok(!result.onDiskAfterAbort.unlocked.includes('Achievement03'));
 assert.deepEqual(result.recovered.pending,[]);assert.equal(result.recovered.error,null);assert.deepEqual(result.reopened.unlocked,['Achievement02','Achievement03','Achievement04','Achievement05','Achievement20','Achievement22']);assert.equal(result.invalid,true);assert.equal(result.unchanged,true);
 assert.deepEqual(errors,[]);assert.deepEqual(hashes(),sourceSha256);
 writeFileSync('docs/porting/th06nc-achievements-browser-verified.json',JSON.stringify({scope:'Local browser platform replacement using actual IndexedDB. Award/commit separation, duplicate suppression, independent writers merge, transaction abort without published unlock, retry, queued commits, validation and independent reload. Score/config unchanged. Native producer conditions have separate checks; Steam/platform/network equivalence excluded.',evidence:result,sourceSha256,passed:true,completeGame:false,nativeEquivalent:false},null,2)+'\n');console.log(JSON.stringify({passed:true,checks:14}));
}finally{socket?.close();child.kill();}
