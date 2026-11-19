// Focused CDP check: wait for actual readiness, then exercise the visible buttons.
import {spawn} from 'node:child_process';
import {existsSync,mkdirSync,mkdtempSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import assert from 'node:assert/strict';
const chrome=['C:/Program Files/Google/Chrome/Application/chrome.exe','C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'].find(existsSync);
if(!chrome)throw Error('No Chrome/Edge');
const home=resolve('artifacts/th06nc/difficulty-sequence-browser');mkdirSync(home,{recursive:true});mkdirSync('tools/tmp',{recursive:true});
const port=9468,profile=mkdtempSync(resolve('tools/tmp/th06nc-menu-'));
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
 await send('Page.navigate',{url:'http://127.0.0.1:8268/runtimes/th06nc/main-menu-lab.html'});
 const observations=[];
 observations.push(await wait('globalThis.mainMenuLabReport?.state===3&&globalThis.mainMenuLabReport'));
 await evaluate("document.querySelector('#confirm').click()");
 observations.push(await wait('globalThis.mainMenuLabReport?.state===9&&globalThis.mainMenuLabReport'));
 await evaluate('globalThis.__entryUpdates=globalThis.mainMenuLabReport.updates');
 // Allow the entry labels to settle before the next input boundary.
 await wait('globalThis.mainMenuLabReport?.state===9&&globalThis.mainMenuLabReport.updates>globalThis.__entryUpdates+40');
 await evaluate("document.querySelector('#down').click()");
 observations.push(await wait('globalThis.mainMenuLabReport?.state===9&&globalThis.mainMenuLabReport.selection===2&&globalThis.mainMenuLabReport'));
 const image=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});writeFileSync(resolve(home,'difficulty-hard.png'),Buffer.from(image.data,'base64'));
 await evaluate("document.querySelector('#confirm').click()");
 observations.push(await wait('globalThis.mainMenuLabReport?.state===11&&globalThis.mainMenuLabReport'));
 const settle=async()=>{await evaluate('globalThis.__entryUpdates=globalThis.mainMenuLabReport.updates');await wait('globalThis.mainMenuLabReport.updates>globalThis.__entryUpdates+32');};
 const click=async(id,state,selection)=>{await evaluate(`document.querySelector('#${id}').click()`);observations.push(await wait(`globalThis.mainMenuLabReport?.state===${state}&&globalThis.mainMenuLabReport.selection===${selection}&&globalThis.mainMenuLabReport`));};
 await settle();
 // Exercise a physical keyboard event as well as the diagnostic buttons.
 await send('Input.dispatchKeyEvent',{type:'keyDown',code:'ArrowRight',key:'ArrowRight',windowsVirtualKeyCode:39});
 await wait('globalThis.mainMenuLabReport.selection===1');
 await send('Input.dispatchKeyEvent',{type:'keyUp',code:'ArrowRight',key:'ArrowRight',windowsVirtualKeyCode:39});
 observations.push(await wait('globalThis.mainMenuLabReport.state===11&&globalThis.mainMenuLabReport.selection===1&&globalThis.mainMenuLabReport'));
 await click('confirm',13,0);await settle();await click('down',13,1);
 const characterShotImage=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});writeFileSync(resolve(home,'character-shot.png'),Buffer.from(characterShotImage.data,'base64'));
 await click('cancel',11,1);await settle();await click('cancel',9,2);await settle();
 await click('confirm',11,1);await settle();await click('confirm',13,1);await settle();await click('confirm',14,0);
 await settle();await click('down',14,1);await click('cancel',13,1);await settle();await click('confirm',14,1);await settle();await click('confirm',24,0);await settle();
 await click('cancel',14,1);await settle();await click('confirm',24,0);await settle();
 const launchImage=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});writeFileSync(resolve(home,'final-confirmation.png'),Buffer.from(launchImage.data,'base64'));
 await click('confirm',25,0);
 observations.push(await wait('globalThis.mainMenuLabReport.gameHandoffReady&&globalThis.mainMenuLabReport'));
 assert.ok(observations.every(o=>o.error===0&&o.drawn>0));assert.equal(observations.at(-1).destinationImplemented,false);assert.equal(observations.at(-1).configuredCharacter,1);assert.equal(observations.at(-1).configuredShot,1);assert.equal(errors.length,0);
 assert.equal(observations.at(-1).fadeMode,2);assert.equal(observations.at(-1).fadeAlpha,255);assert.equal(observations.at(-1).background,'select00');
 const report={scope:'Visible Start -> Hard -> character keyboard switch -> shot switch -> two-level return -> saved character/shot -> mode switch and return -> saved mode -> final confirmation and return -> full fade to game handoff request. Native startup, actual game handoff, audio and native pixels incomplete.',observations,errors,passed:true,completeGame:false,nativeEquivalent:false};
 writeFileSync(resolve(home,'report.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:true,states:observations.map(o=>o.state),selections:observations.map(o=>o.selection),completeGame:false}));
}catch(error){
 // Preserve failure evidence without turning the absence of exceptions into success.
 writeFileSync(resolve(home,'failure.txt'),String(error.stack));throw error;
}finally{if(socket)socket.close();child.kill();}
