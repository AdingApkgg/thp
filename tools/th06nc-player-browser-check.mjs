// Focused CDP check: wait for actual readiness, then exercise the visible buttons.
import {spawn} from 'node:child_process';
import {existsSync,mkdirSync,mkdtempSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import assert from 'node:assert/strict';
const chrome=['C:/Program Files/Google/Chrome/Application/chrome.exe','C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'].find(existsSync);
if(!chrome)throw Error('No Chrome/Edge');
const home=resolve('artifacts/th06nc/player-browser');mkdirSync(home,{recursive:true});mkdirSync('tools/tmp',{recursive:true});
const port=9480,profile=mkdtempSync(resolve('tools/tmp/th06nc-player-'));
const child=spawn(chrome,['--headless=new','--no-sandbox','--enable-unsafe-swiftshader','--mute-audio','--no-first-run',`--remote-debugging-port=${port}`,`--user-data-dir=${profile}`,'about:blank'],{stdio:'ignore'});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));let socket;
try{
 let target;const deadline=Date.now()+20000;
 while(Date.now()<deadline){try{target=(await(await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(t=>t.type==='page');if(target)break;}catch{}await sleep(200);}
 if(!target)throw Error('Browser target not ready');
 socket=new WebSocket(target.webSocketDebuggerUrl);await new Promise((ok,bad)=>{socket.onopen=ok;socket.onerror=bad;});
 let id=0;const pending=new Map(),errors=[];
 socket.onmessage=e=>{const m=JSON.parse(e.data);if(m.id){const p=pending.get(m.id);if(p){pending.delete(m.id);m.error?p.reject(Error(m.error.message)):p.resolve(m.result);}}else if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails.exception?.description??m.params.exceptionDetails.text);};
 const send=(method,params={})=>new Promise((resolve,reject)=>{const n=++id;pending.set(n,{resolve,reject});socket.send(JSON.stringify({id:n,method,params}));});
 const evaluate=async expression=>{const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(r.exceptionDetails.exception?.description??r.exceptionDetails.text);return r.result.value;};
 const wait=async expression=>{const until=Date.now()+40000;while(Date.now()<until){if(errors.length)throw Error(errors.join('\n'));const v=await evaluate(expression);if(v)return v;await sleep(100);}throw Error('Timed out: '+expression);};
 await send('Runtime.enable');await send('Page.enable');await send('Emulation.setDeviceMetricsOverride',{width:1100,height:1100,deviceScaleFactor:1,mobile:false});
 await send('Page.navigate',{url:'http://127.0.0.1:8268/runtimes/th06nc/player-lab.html'});
 const observations=[];
 await wait('globalThis.playerLabReport?.ready&&globalThis.playerLabReport');
 for(const character of [0,1])for(const shot of [0,1]){
  await evaluate(`document.querySelector('button[data-player="${character},${shot}"]').click()`);
  const start=await wait(`globalThis.playerLabReport?.character===${character}&&globalThis.playerLabReport?.shot===${shot}&&globalThis.playerLabReport?.frame===0&&globalThis.playerLabReport`);
  const keys=[{key:'ArrowRight',code:'ArrowRight',windowsVirtualKeyCode:39,nativeVirtualKeyCode:39},{key:'z',code:'KeyZ',windowsVirtualKeyCode:90,nativeVirtualKeyCode:90},{key:'Shift',code:'ShiftLeft',windowsVirtualKeyCode:16,nativeVirtualKeyCode:16}];
  for(const key of keys)await send('Input.dispatchKeyEvent',{type:'keyDown',...key});
  await evaluate(`document.querySelector('#step').click()`);const held=await wait('globalThis.playerLabReport?.frame===60&&globalThis.playerLabReport');
  assert.equal(held.position[0],start.position[0]+(character===0?120:150));assert.equal(held.position[1],start.position[1]);assert.equal(held.focus,true);assert.ok(held.activeShots>0);assert.ok(held.coloredPixels>40);assert.equal(held.glError,0);
  const picture=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});writeFileSync(resolve(home,`player-${character}-${shot}.png`),Buffer.from(picture.data,'base64'));
  for(const key of keys)await send('Input.dispatchKeyEvent',{type:'keyUp',...key});
  await evaluate(`document.querySelector('#step').click()`);const released=await wait('globalThis.playerLabReport?.frame===120&&globalThis.playerLabReport');assert.deepEqual(released.position,held.position);assert.equal(released.focus,false);
  await evaluate(`document.querySelector('#step').click()`);const end=await wait('globalThis.playerLabReport?.frame===180&&globalThis.playerLabReport');assert.deepEqual(end.position,held.position);assert.equal(end.glError,0);for(let count=0;count<5;count++)await evaluate(`document.querySelector('#step').click()`);const settled=await wait('globalThis.playerLabReport?.frame===480&&globalThis.playerLabReport');assert.equal(settled.activeShots,0);assert.equal(settled.glError,0);observations.push({character,shot,start,held,released,end,settled});
 }
 assert.equal(errors.length,0);
 const report={scope:'Real player ANM/DDS, all four profiles, actual browser keyDown/keyUp for arrows/Z/Shift and visible frame-step buttons. Checks movement, focus, active shots, pixels and GL errors; native pixel equivalence, wall-clock timing and complete game excluded.',observations,errors,passed:true,completeGame:false,nativeEquivalent:false};
 writeFileSync(resolve(home,'report.json'),JSON.stringify(report,null,2)+'\n');writeFileSync(resolve('docs/porting/th06nc-player-browser-observed.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
}catch(error){writeFileSync(resolve(home,'failure.txt'),String(error.stack));throw error;}finally{if(socket)socket.close();child.kill();}
