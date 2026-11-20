import {chromium} from 'playwright-core';
import {mkdir,writeFile,readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
const option=(name,fallback)=>process.argv.find(a=>a.startsWith('--'+name+'='))?.slice(name.length+3)??fallback;
const base=option('url',process.env.TH14_FULL_REPLAY_BASE??'http://localhost:8257/?game=th14');
const out=new URL('../artifacts/th14/'+option('output',process.env.TH14_FULL_REPLAY_OUTPUT??'natural-browser-extra-nov18')+'/',import.meta.url);await mkdir(out,{recursive:false});
const report={schema:'th14/native-extra-gpu/1',startedAt:new Date().toISOString(),url:base,scope:'Fresh isolated headless Chrome; actual packaged launcher UI, no existing user browser',steps:[],errors:[],consoleErrors:[],httpErrors:[],delivery:[],passed:false};
const source=await readFile(new URL(import.meta.url));report.harnessSha256=createHash('sha256').update(source).digest('hex');await writeFile(new URL('harness.mjs',out),source);
const save=()=>writeFile(new URL('report.json',out),JSON.stringify(report,null,2));
const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',args:['--enable-gpu','--use-gl=angle','--use-angle=d3d11','--mute-audio','--disable-frame-rate-limit','--disable-gpu-vsync']});let page;
try{
 report.browser=browser.version();const context=await browser.newContext({viewport:{width:1280,height:900}});await context.addInitScript(({clock})=>{
 if(window===parent)return;window.__naturalClock={declared:clock,calls:0,patchedImports:0};
 const patch=imports=>{if(typeof imports?.env?.th14_clock_ticks==='function'){imports.env.th14_clock_ticks=()=>{__naturalClock.calls++;return clock;};__naturalClock.patchedImports++;}return imports;};
 const instantiate=WebAssembly.instantiate;WebAssembly.instantiate=function(source,imports){return instantiate.call(this,source,patch(imports));};
 const streaming=WebAssembly.instantiateStreaming;WebAssembly.instantiateStreaming=function(source,imports){return streaming.call(this,source,patch(imports));};
 },{clock:Number(process.env.TH14_NATURAL_CLOCK??241201554)});page=await context.newPage();
 page.on('pageerror',e=>report.errors.push(String(e)));page.on('console',m=>{if(m.type()==='error')report.consoleErrors.push(m.text());});
 const pending=[];page.on('response',r=>{if(r.status()>=400)report.httpErrors.push({url:r.url(),status:r.status()});if(r.status()===200&&new URL(r.url()).origin===new URL(base).origin&&/^\/(?:assets\/|runtime\/th14\/)/.test(new URL(r.url()).pathname)&&/\.(?:js|mjs|wasm)$/.test(new URL(r.url()).pathname))pending.push((async()=>{const b=await r.body();report.delivery.push({url:r.url(),bytes:b.length,sha256:createHash('sha256').update(b).digest('hex')});})().catch(e=>{(report.captureErrors??=[]).push(String(e));}));});
 async function step(name,operation){console.log(name);const started=Date.now();try{const observation=await operation();report.steps.push({name,passed:true,elapsedMs:Date.now()-started,observation});await save();return observation;}catch(e){report.steps.push({name,passed:false,error:String(e.stack)});throw e;}}
 await step('fresh-launcher-and-zero-volume',async()=>{
  await page.goto(base,{waitUntil:'networkidle',timeout:45000});
  await page.locator('#firstUseNoticeCloseHint').click();
  await page.getByRole('button',{name:'音量设置',exact:true}).click();
  const sliders=page.getByRole('slider');await sliders.first().waitFor();
  for(let i=0;i<await sliders.count();i++){await sliders.nth(i).focus();await sliders.nth(i).press('Home');}
  const volumes=await sliders.evaluateAll(es=>es.map(e=>({label:e.getAttribute('aria-label'),value:e.getAttribute('aria-valuenow')})));
  if(!volumes.some(v=>v.label==='游戏音乐')||!volumes.some(v=>v.label==='游戏音效')||volumes.some(v=>v.value!=='0'))throw Error('Volume controls not all zero: '+JSON.stringify(volumes));
  return{volumes,isolated:await page.evaluate(()=>crossOriginIsolated)};
 });
 await step('ui-launch-no-music',async()=>{
  await page.getByRole('button',{name:'高级设置',exact:true}).click();await page.locator('#musicSelect-trigger').click();await page.locator('[role="option"][data-value="none"]').click();

  await step('import-real-normal-clear-save-through-ui',async()=>{
   const b=await readFile(process.env.TH14_NATURAL_SOURCE_SAVE),hash=createHash('sha256').update(b).digest('hex');if(hash!=='4c0e43f0d91f518fd5e0a243c1763980e58bded7281fceacf97b6abb8841bc33')throw Error('Earned Normal score identity differs');
   const group=page.locator('[id$="fileOptions"]');const toggle=group.locator('button[aria-expanded]').first();if(await toggle.count()&&await toggle.getAttribute('aria-expanded')==='false')await toggle.click();
   const chooser=page.waitForEvent('filechooser',{timeout:30000});await page.locator('[id$="saveFileTool"] [data-action="import-save"]').click();
   const d=page.locator('#decisionDialog[open]:not(.closing)');await d.waitFor();await d.locator('#decisionConfirm').click();await(await chooser).setFiles({name:'scoreth14.dat',mimeType:'application/octet-stream',buffer:b});
   await page.waitForFunction(()=>document.querySelector('#status')?.textContent?.includes('已导入'),null,{timeout:120000});report.normalSourceScoreSha256=hash;return{bytes:b.length,sha256:hash,actualEarnedNormalSave:true,status:await page.locator('#status').textContent()};
  });
  await page.locator('#launch').click();
  const deadline=Date.now()+120000;
  while(Date.now()<deadline){
   const dialog=page.locator('#decisionDialog[open]:not(.closing)');
   if(await dialog.count()){const text=await dialog.innerText();report.steps.push({name:'launcher-decision',text});await dialog.locator('#decisionConfirm').click();}
   if(await page.evaluate(()=>!!document.querySelector('#gameFrame')?.contentWindow?.core?.th11_phase))break;
   await page.waitForTimeout(200);
  }
  await page.locator('#gameFrame').click({position:{x:100,y:100},timeout:15000});
  await page.waitForFunction(()=>{const c=document.querySelector('#gameFrame')?.contentWindow?.core;return c?.th11_phase?.()===0&&c.th11_title(0)===1&&c.th11_title(1)===2;},null,{timeout:90000});
  return page.evaluate(()=>{const w=document.querySelector('#gameFrame').contentWindow,m=w.Module;return{src:w.location.href,phase:w.core.th11_phase(),title:[0,1,2,3,4].map(k=>w.core.th11_title(k)),audio:m?.SDL3?.audioContext?.state};});
 });
 await page.screenshot({path:fileURLToPath(new URL('title-private.png',out))});
 const snapshot=()=>page.evaluate(()=>{const w=document.querySelector('#gameFrame')?.contentWindow,c=w?.core;return c?{phase:c.th11_phase(),stage:c.th11_stage(),frame:c.th11_frame(),title:[0,1,2,3,4].map(k=>c.th11_title(k)),error:w.document.querySelector('#error')?.textContent}:null;});
 const key=async name=>{await page.keyboard.down(name);await page.waitForTimeout(70);await page.keyboard.up(name);await page.waitForTimeout(600);};

 async function titleReady(screen){await page.waitForFunction(screen=>{const c=document.querySelector('#gameFrame')?.contentWindow?.core;return c?.th11_phase?.()===0&&c.th11_title(0)===screen&&c.th11_title(1)===2;},screen,{timeout:15000});}
 async function cursor(screen,target,direction){await titleReady(screen);for(let tries=0;tries<5;tries++){if((await snapshot()).title[2]===target)return;await key(direction);}throw Error('Menu cursor failed '+screen+'/'+target);}



 const state=()=>page.evaluate(()=>{const w=document.querySelector('#gameFrame').contentWindow,m=w.Module;return{v:Array.from({length:50},(_,i)=>m._th14_acceptance_natural_state(i)),frame:w.core.th11_frame(),clock:w.__naturalClock,error:w.document.querySelector('#error')?.textContent};});
 const imported=await state();if(imported.v[46]!==1||imported.v[47]!==0||imported.v[49]!==17)throw Error('Earned Normal unlock was not loaded '+JSON.stringify(imported));report.importedNormalNativeState=imported;
 const input=await readFile(process.env.TH14_NATURAL_KEYS);report.inputSha256=createHash('sha256').update(input).digest('hex');if(report.inputSha256!=='3979ae43be068d2fff96ddf432d0363e9677b8c39e9901ea3c49331c4858aca1')throw Error('Extra input identity differs');
 await step('load-independent-extra-held-mask-source',async()=>page.evaluate(data=>{const m=document.querySelector('#gameFrame').contentWindow.Module;return m.th14AsyncRuntime.run(()=>{const p=m._malloc(data.length);try{m.HEAPU8.set(data,p);if(m._th14_acceptance_load_keys(p,data.length)!==1)throw Error('Extra keys rejected');return{accepted:true,bytes:data.length};}finally{m._free(p);}});},Array.from(input)));
 await step('real-extra-character-partner-menus',async()=>{await cursor(1,1,'ArrowDown');await key('z');await cursor(5,0,'ArrowUp');await key('z');await cursor(6,0,'ArrowRight');await key('z');await cursor(7,1,'ArrowRight');await key('z');await page.waitForFunction(()=>document.querySelector('#gameFrame').contentWindow.Module._th14_acceptance_natural_state(7)>=32,null,{timeout:90000});const f=await state();if(f.v[1]!==7||f.v[28]<32)throw Error('Extra did not begin '+JSON.stringify(f));return f;});
 const factor=Number(process.env.TH14_NATURAL_FRAME_FACTOR??8);await page.evaluate(factor=>{const r=document.querySelector('#gameFrame').contentWindow.Module.th14AsyncRuntime,original=r.requestFrame;r.requestFrame=callback=>original(time=>callback(time*factor));},factor);report.hostDisplayClockFactor=factor;report.nativeRafLoopUnchanged=true;report.noCompletionEventsOrGameStateWrites=true;report.physicalRealtimePerformanceClaimed=false;report.progress=[];
 const began=Date.now(),deadline=began+1400000;let logged=0,complete=null;
 while(Date.now()<deadline){const f=await state();if(f.error||report.errors.length)throw Error('Runtime error '+JSON.stringify(f));if(f.v.slice(24,28).some(Boolean))throw Error('Nonordinary Extra mode '+JSON.stringify(f));if(f.v[7]>90000)throw Error('Extra callback bound');
  if(f.v[0]===3){if(f.v[43]!==1){report.naturalGameOver=f;throw Error('Natural Extra Game Over before clear');}complete=f;break;}
  if(f.v[0]===5)throw Error('Extra unexpectedly entered Normal Ending');
  if(!report.stageImage&&f.v[0]===1&&f.v[1]===7&&f.v[3]>=240&&f.v[4]&&!f.v[5]){const b=await page.screenshot({path:fileURLToPath(new URL('extra-stage-private.png',out))});report.stageImage={state:f,sha256:createHash('sha256').update(b).digest('hex')};await save();}
  if(Date.now()-logged>=10000){const q={seconds:(Date.now()-began)/1000,stage:f.v[1],phase:f.v[0],callbacks:f.v[7],recordedFrames:f.v[3],score:f.v[10]*10,lives:f.v[12]|0};report.progress.push(q);await save();console.log(JSON.stringify(q));logged=Date.now();}await page.waitForTimeout(200);
 }
 if(!complete||complete.v[17]!==128)throw Error('Natural Extra clear not observed');report.extraCompleted=complete;
 async function pauseReady(expected){await page.waitForFunction(expected=>{const m=document.querySelector('#gameFrame').contentWindow.Module;return m._th14_acceptance_natural_state(39)===expected&&m._th14_acceptance_natural_state(40)>=12;},expected,{timeout:15000});}
 await pauseReady(25);await page.waitForTimeout(1000);report.extraRankUi=await state();await page.screenshot({path:fileURLToPath(new URL('extra-result-name-private.png',out))});
 for(let i=0;i<12&&(await state()).v[39]===25;i++)await key('z');await pauseReady(22);if((await state()).v[41]!==0)throw Error('Unexpected Extra end menu cursor');await key('ArrowDown');await key('z');await pauseReady(23);await page.screenshot({path:fileURLToPath(new URL('extra-replay-slots-private.png',out))});await key('z');await pauseReady(24);
 for(let i=0;i<12&&(await state()).v[39]===24;i++)await key('z');await pauseReady(23);await key('x');await pauseReady(22);if((await state()).v[41]===1)await key('ArrowUp');if((await state()).v[41]!==0)throw Error('Extra return title selection failed');await key('z');await titleReady(1);report.nativeExtraMenusPassed=true;report.afterExtraNativeState=await state();
 const files=()=>page.evaluate(()=>{const fs=document.querySelector('#gameFrame').contentWindow.Module.FS;const roots=fs.readdir('/save').filter(n=>/^(?:score.*\.dat|th14\.cfg)$/.test(n)).map(n=>'/save/'+n);const replays=fs.readdir('/save/replay').filter(n=>/^th14.*\.rpy$/.test(n)).map(n=>'/save/replay/'+n);return[...roots,...replays].map(path=>({name:path.split('/').at(-1),bytes:Array.from(fs.readFile(path))}));});
 const dump=async label=>{const rows=[];for(const f of await files()){const b=Buffer.from(f.bytes);await writeFile(new URL(label+'-'+f.name+'-private.bin',out),b);rows.push({name:f.name,bytes:b.length,sha256:createHash('sha256').update(b).digest('hex')});}return rows;};
 report.savedFiles=await dump('written');if(!report.savedFiles.some(x=>/\.rpy$/.test(x.name)))throw Error('Extra native replay not saved');await key('Escape');await key('z');await page.waitForFunction(()=>!document.querySelector('#player')?.classList.contains('open'),null,{timeout:15000});
 await page.reload({waitUntil:'networkidle'});await page.locator('#launch').click();const loadDeadline=Date.now()+120000;while(Date.now()<loadDeadline){const d=page.locator('#decisionDialog[open]:not(.closing)');if(await d.count())await d.locator('#decisionConfirm').click();if(await page.evaluate(()=>!!document.querySelector('#gameFrame')?.contentWindow?.core?.th11_phase))break;await page.waitForTimeout(200);}await page.locator('#gameFrame').click({position:{x:100,y:100}});await titleReady(1);
 report.freshFiles=await dump('fresh');report.freshNativeState=await state();if(report.freshNativeState.v[46]!==1||report.freshNativeState.v[47]!==1||report.freshNativeState.v[49]!==17)throw Error('Fresh Extra statistics or Normal unlock changed');for(const a of report.savedFiles)if(!report.freshFiles.some(b=>b.name===a.name&&b.sha256===a.sha256))throw Error('Fresh saved file identity differs '+a.name);await page.screenshot({path:fileURLToPath(new URL('extra-fresh-title-private.png',out))});await key('Escape');await key('z');await page.waitForFunction(()=>!document.querySelector('#player')?.classList.contains('open'),null,{timeout:15000});
 await Promise.all(pending);if(report.errors.length||report.captureErrors?.length)throw Error('Page or delivery errors');report.passed=true;report.fullNaturalExtraAccepted=true;report.visualInspectionPending=true;report.semanticSaveQualificationPending=true;
}catch(e){report.failure=String(e.stack);if(page){report.failureUi=await page.evaluate(()=>({text:document.body.innerText.slice(-2200),frames:[...document.querySelectorAll('iframe')].map(e=>({src:e.src,error:e.contentWindow?.document.querySelector('#error')?.textContent,phase:e.contentWindow?.core?.th11_phase?.()}))})).catch(()=>null);await page.screenshot({path:fileURLToPath(new URL('failure-private.png',out))}).catch(()=>{});}process.exitCode=1;}finally{await save();await browser.close();console.log(JSON.stringify({passed:report.passed,extraCompleted:report.extraCompleted,latest:report.progress?.at(-1),failure:report.failure}));}
