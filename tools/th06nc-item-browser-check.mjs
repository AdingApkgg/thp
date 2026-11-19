// Focused CDP check: wait for actual readiness, then exercise the visible buttons.
import {spawn} from 'node:child_process';
import {existsSync,mkdirSync,mkdtempSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import assert from 'node:assert/strict';
const chrome=['C:/Program Files/Google/Chrome/Application/chrome.exe','C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'].find(existsSync);
if(!chrome)throw Error('No Chrome/Edge');
const home=resolve('artifacts/th06nc/item-browser');mkdirSync(home,{recursive:true});mkdirSync('tools/tmp',{recursive:true});
const port=9481,profile=mkdtempSync(resolve('tools/tmp/th06nc-item-'));
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
 await send('Page.navigate',{url:'http://127.0.0.1:8268/runtimes/th06nc/item-lab.html'});
 const observations=[];
 await wait('globalThis.itemLabReport?.ready&&globalThis.itemLabReport');
 for(const mode of ['normal','arrows','collect','scatter']){
  await evaluate(`document.querySelector('button[data-mode="${mode}"]').click()`);const start=await wait(`globalThis.itemLabReport?.mode==='${mode}'&&globalThis.itemLabReport?.frame===0&&globalThis.itemLabReport`);
  assert.equal(start.activeItems,7);assert.equal(start.itemDrawCalls,7);assert.ok(start.coloredPixels>100);assert.equal(start.glError,0);
  const picture=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});writeFileSync(resolve(home,`${mode}.png`),Buffer.from(picture.data,'base64'));
  await evaluate(`document.querySelector('#step').click()`);const middle=await wait('globalThis.itemLabReport?.frame===30&&globalThis.itemLabReport');
  await evaluate(`document.querySelector('#step').click()`);const end=await wait('globalThis.itemLabReport?.frame===60&&globalThis.itemLabReport');assert.equal(end.glError,0);
  let settled=null;
  if(mode==='collect'){
   assert.equal(end.activeItems,0);assert.equal(end.power,128);assert.equal(end.lives,3);assert.equal(end.bombs,3);assert.equal(end.pointStage,1);assert.ok(BigInt(end.score)>0n);assert.ok(end.conversions>0);assert.ok(end.popupCount>=5);assert.ok(middle.popupDrawCalls>0);assert.ok(end.popupDrawCalls>0);
   const picture=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});writeFileSync(resolve(home,'collected-popups.png'),Buffer.from(picture.data,'base64'));
   await evaluate(`document.querySelector('#step').click();document.querySelector('#step').click()`);settled=await wait('globalThis.itemLabReport?.frame===120&&globalThis.itemLabReport');assert.equal(settled.popupDrawCalls,0);assert.equal(settled.glError,0);
  }else assert.equal(end.activeItems,7);
  observations.push({mode,start,middle,end,settled});
 }
 assert.equal(errors.length,0);
 const report={scope:'Real seven-item/player ANM/DDS and ASCII popup glyphs. Visible controls exercise falling, above-screen arrows, POC homing, death scatter and all seven pickups; checks power, lives, bombs, points, score, popup rendering/expiry, pixels and GL errors. Native pixel equivalence and complete game excluded.',observations,errors,passed:true,completeGame:false,nativeEquivalent:false};
 writeFileSync(resolve(home,'report.json'),JSON.stringify(report,null,2)+'\n');writeFileSync(resolve('docs/porting/th06nc-item-browser-observed.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
}catch(error){writeFileSync(resolve(home,'failure.txt'),String(error.stack));throw error;}finally{if(socket)socket.close();child.kill();}
