import {spawn} from 'node:child_process';
import {existsSync,mkdtempSync,mkdirSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
const args=Object.fromEntries(process.argv.slice(2).map(x=>{const i=x.indexOf('=');return [x.slice(2,i),x.slice(i+1)];}));
const chrome=['C:/Program Files/Google/Chrome/Application/chrome.exe','C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'].find(existsSync);
const port=Number(args.port??9507),dir=resolve(args.output??'artifacts/th06nc/launcher-browser');mkdirSync(dir,{recursive:true});
const profile=args.profile??mkdtempSync(resolve('tools/tmp/th06nc-launcher-chrome-'));writeFileSync(resolve(dir,'profile.txt'),profile);
const child=spawn(chrome,['--headless=new','--no-sandbox','--enable-unsafe-swiftshader','--autoplay-policy=no-user-gesture-required','--no-first-run',`--remote-debugging-port=${port}`,'--user-data-dir='+profile,'about:blank'],{stdio:'ignore'});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));let socket;
try{
 let tab;for(let n=0;n<100;n++){try{tab=(await(await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(t=>t.type==='page');if(tab)break;}catch{}await sleep(100);}
 socket=new WebSocket(tab.webSocketDebuggerUrl);await new Promise((yes,no)=>{socket.onopen=yes;socket.onerror=no;});let serial=0;const pending=new Map(),errors=[],messages=[];
 socket.onmessage=event=>{const message=JSON.parse(event.data);if(message.id){const task=pending.get(message.id);pending.delete(message.id);message.error?task.reject(Error(message.error.message)):task.resolve(message.result);}else{if(message.method==='Runtime.exceptionThrown')errors.push(message.params.exceptionDetails.exception?.description??message.params.exceptionDetails.text);if(message.method==='Runtime.consoleAPICalled')messages.push(message.params.args.map(x=>x.value??x.description).join(' '));}};
 const send=(method,params={})=>new Promise((resolve,reject)=>{const id=++serial;pending.set(id,{resolve,reject});socket.send(JSON.stringify({id,method,params}));});
 const evaluate=async expression=>{const result=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true,userGesture:true});if(result.exceptionDetails)throw Error(result.exceptionDetails.exception?.description??result.exceptionDetails.text);return result.result.value;};
 const picture=async name=>{const result=await send('Page.captureScreenshot',{format:'png'});writeFileSync(resolve(dir,name+'.png'),Buffer.from(result.data,'base64'));};
 const wait=async(expression,timeout=180000)=>{const start=Date.now();while(Date.now()-start<timeout){if(await evaluate('Boolean('+expression+')'))return;await sleep(200);}throw Error('Timeout: '+expression+'\n'+JSON.stringify({errors,messages,body:await evaluate('document.body?.innerText.slice(0,3500)')}));};
 await send('Page.enable');await send('Runtime.enable');await send('Network.enable');await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false});
 await send('Page.navigate',{url:args.url});
 await (await import(pathToFileURL(resolve(args.scenario)))).default({send,evaluate,picture,wait,sleep,dir,errors,messages});
 writeFileSync(resolve(dir,'browser-log.json'),JSON.stringify({errors,messages},null,2));
}catch(error){writeFileSync(resolve(dir,'failure.txt'),String(error.stack));throw error;}finally{socket?.close();child.kill();}
