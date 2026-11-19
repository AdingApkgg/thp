// Focused CDP check: wait for actual readiness, then exercise the visible buttons.
import {spawn} from 'node:child_process';
import {existsSync,mkdirSync,mkdtempSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import assert from 'node:assert/strict';
const chrome=['C:/Program Files/Google/Chrome/Application/chrome.exe','C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'].find(existsSync);
if(!chrome)throw Error('No Chrome/Edge');
const home=resolve('artifacts/th06nc/message-browser');mkdirSync(home,{recursive:true});mkdirSync('tools/tmp',{recursive:true});
const port=9482,profile=mkdtempSync(resolve('tools/tmp/th06nc-message-'));
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
 await send('Page.navigate',{url:'http://127.0.0.1:8268/runtimes/th06nc/message-lab.html'});
 const observations=[];
 await wait('globalThis.messageLabReport?.ready&&globalThis.messageLabReport');
 for(const stage of [1,2,3,4,5,6])for(const character of [0,1]){
  await evaluate(`document.querySelector('#stage').value='${stage}';document.querySelector('#stage').dispatchEvent(new Event('change'));document.querySelector('[data-character="${character}"]').click()`);const start=await wait(`globalThis.messageLabReport?.stage===${stage}&&globalThis.messageLabReport?.character===${character}&&globalThis.messageLabReport?.frame===0&&globalThis.messageLabReport`);
  await evaluate(`for(let i=0;i<3;i++)document.querySelector('[data-step="30"]').click()`);const first=await wait('globalThis.messageLabReport?.frame===90&&globalThis.messageLabReport');assert.ok(first.paintCount>0);assert.ok(first.textPixels>50);assert.ok(first.textDrawCalls>0);assert.ok(first.drawCalls>=3);assert.equal(first.glError,0);assert.ok(first.lines.some(l=>l&&l.text!==l.key));
  const picture=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});writeFileSync(resolve(home,`stage-${stage}-character-${character}.png`),Buffer.from(picture.data,'base64'));
  const key={key:'z',code:'KeyZ',windowsVirtualKeyCode:90,nativeVirtualKeyCode:90};await send('Input.dispatchKeyEvent',{type:'keyDown',...key});await evaluate(`document.querySelector('[data-step="1"]').click();document.querySelector('[data-step="1"]').click()`);const advanced=await wait('globalThis.messageLabReport?.frame===92&&globalThis.messageLabReport');await send('Input.dispatchKeyEvent',{type:'keyUp',...key});assert.ok(advanced.lines.some((l,i)=>l?.key!==first.lines[i]?.key));assert.equal(advanced.glError,0);
  const ctrl={key:'Control',code:'ControlLeft',windowsVirtualKeyCode:17,nativeVirtualKeyCode:17};await send('Input.dispatchKeyEvent',{type:'keyDown',...ctrl});await evaluate(`document.querySelector('[data-step="300"]').click()`);const end=await wait('globalThis.messageLabReport?.frame===392&&globalThis.messageLabReport');await send('Input.dispatchKeyEvent',{type:'keyUp',...ctrl});assert.equal(end.id,-1);assert.equal(end.drawCalls,0);assert.equal(end.glError,0);assert.ok(end.musicRequests.length>0);observations.push({stage,character,start,first,advanced,end});
 }
 assert.equal(errors.length,0);
 const report={scope:'Native resource bases, real portrait/message/text ANM, original zh-CN font atlas bitmaps and localization. Six stages/two characters exercise visible frame controls and trusted Z/Ctrl input; checks glyph texture pixels, draw calls, page advance, dialog completion, music requests and GL errors. Canvas source-over composition is used; native GPU pixel equivalence, audio playback and complete game excluded.',observations,errors,passed:true,completeGame:false,nativeEquivalent:false};
 writeFileSync(resolve(home,'report.json'),JSON.stringify(report,null,2)+'\n');writeFileSync(resolve('docs/porting/th06nc-message-browser-observed.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
}catch(error){writeFileSync(resolve(home,'failure.txt'),String(error.stack));throw error;}finally{if(socket)socket.close();child.kill();}
