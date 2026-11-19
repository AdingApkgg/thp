// Focused CDP check: wait for actual readiness, then exercise the visible buttons.
import {spawn} from 'node:child_process';
import {existsSync,mkdirSync,mkdtempSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import assert from 'node:assert/strict';
const chrome=['C:/Program Files/Google/Chrome/Application/chrome.exe','C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'].find(existsSync);
if(!chrome)throw Error('No Chrome/Edge');
const home=resolve('artifacts/th06nc/std-browser');mkdirSync(home,{recursive:true});mkdirSync('tools/tmp',{recursive:true});
const port=9484,profile=mkdtempSync(resolve('tools/tmp/th06nc-std-'));
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
 await send('Page.navigate',{url:'http://127.0.0.1:8268/runtimes/th06nc/std-lab.html'});
 const observations=[];
 await wait('globalThis.stdLabReport?.ready&&globalThis.stdLabReport');
 for(const stage of [1,2,3,4,5,6,7]){
  await evaluate(`document.querySelector('#stage').value='${stage}';document.querySelector('#stage').dispatchEvent(new Event('change'))`);const start=await wait(`globalThis.stdLabReport?.stage===${stage}&&globalThis.stdLabReport?.frame===0&&globalThis.stdLabReport`);assert.equal(start.glError,0);
  await evaluate(`document.querySelector('[data-step="60"]').click()`);const first=await wait('globalThis.stdLabReport?.frame===60&&globalThis.stdLabReport');assert.ok(first.variedPixels>100);assert.ok(first.worldCalls+first.screenCalls>0);assert.equal(first.glError,0);
  const picture=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});writeFileSync(resolve(home,`stage-${stage}.png`),Buffer.from(picture.data,'base64'));
  await evaluate(`document.querySelector('[data-step="300"]').click()`);const advanced=await wait('globalThis.stdLabReport?.frame===360&&globalThis.stdLabReport');assert.equal(advanced.glError,0);assert.ok(advanced.variedPixels>100);
  await evaluate(`document.querySelector('#signal').click()`);const signaled=await wait('globalThis.stdLabReport?.frame===361&&globalThis.stdLabReport');assert.equal(signaled.glError,0);await evaluate(`document.querySelector('#spell-start').click()`);const spellStart=await wait('globalThis.stdLabReport?.spellMode===1&&globalThis.stdLabReport');assert.equal(spellStart.overlayCalls,1);assert.equal(spellStart.coverAlpha,0);assert.equal(spellStart.glError,0);
  await evaluate(`document.querySelector('[data-step="60"]').click();document.querySelector('[data-step="1"]').click()`);const spellActive=await wait('globalThis.stdLabReport?.spellMode===2&&globalThis.stdLabReport');assert.equal(spellActive.spellFrame,61);assert.equal(spellActive.worldCalls,0);assert.equal(spellActive.overlayCalls,1);assert.ok(spellActive.variedPixels>100);assert.equal(spellActive.glError,0);const overlayPicture=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});writeFileSync(resolve(home,`stage-${stage}-spell.png`),Buffer.from(overlayPicture.data,'base64'));
  await evaluate(`document.querySelector('#spell-end').click()`);const spellEnd=await wait('globalThis.stdLabReport?.spellMode===0&&globalThis.stdLabReport');assert.ok(spellEnd.worldCalls+spellEnd.screenCalls>0);assert.equal(spellEnd.overlayCalls,0);assert.equal(spellEnd.glError,0);observations.push({stage,start,first,advanced,signaled,spellStart,spellActive,spellEnd});
 }
 assert.equal(errors.length,0);
 const report={scope:'All seven real STD backgrounds, original ANM/DDS textures, native-derived camera and instance traversal in WebGL2. Visible controls, animation, external wait signal, spell start/61-frame transition/base hiding/overlay/end restoration, non-uniform framebuffer pixels and GL/runtime errors checked. Fog/sampling/depth and final native GPU pixel equivalence remain unverified; full gameplay excluded.',observations,errors,passed:true,completeGame:false,nativeEquivalent:false};
 writeFileSync(resolve(home,'report.json'),JSON.stringify(report,null,2)+'\n');writeFileSync(resolve('docs/porting/th06nc-std-browser-observed.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
}catch(error){writeFileSync(resolve(home,'failure.txt'),String(error.stack));throw error;}finally{if(socket)socket.close();child.kill();}
