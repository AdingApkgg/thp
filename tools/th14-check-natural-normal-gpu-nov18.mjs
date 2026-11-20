import {chromium} from 'playwright-core';
import {mkdir,writeFile,readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
const option=(name,fallback)=>process.argv.find(a=>a.startsWith('--'+name+'='))?.slice(name.length+3)??fallback;
const base=option('url',process.env.TH14_FULL_REPLAY_BASE??'http://localhost:8257/?game=th14');
const out=new URL('../artifacts/th14/'+option('output',process.env.TH14_FULL_REPLAY_OUTPUT??'natural-browser-normal-nov18')+'/',import.meta.url);await mkdir(out,{recursive:false});
const report={schema:'th14/launcher-normal/1',startedAt:new Date().toISOString(),url:base,scope:'Fresh isolated headless Chrome; actual packaged launcher UI, no existing user browser',steps:[],errors:[],consoleErrors:[],httpErrors:[],delivery:[],passed:false};
const source=await readFile(new URL(import.meta.url));report.harnessSha256=createHash('sha256').update(source).digest('hex');await writeFile(new URL('harness.mjs',out),source);
const save=()=>writeFile(new URL('report.json',out),JSON.stringify(report,null,2));
const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',args:['--enable-gpu','--use-gl=angle','--use-angle=d3d11','--mute-audio','--disable-frame-rate-limit','--disable-gpu-vsync']});let page;
try{
 report.browser=browser.version();const context=await browser.newContext({viewport:{width:1280,height:900}});await context.addInitScript(({clock})=>{
 if(window===parent)return;window.__naturalClock={declared:clock,calls:0,patchedImports:0};
 const patch=imports=>{if(typeof imports?.env?.th14_clock_ticks==='function'){imports.env.th14_clock_ticks=()=>{__naturalClock.calls++;return clock;};__naturalClock.patchedImports++;}return imports;};
 const instantiate=WebAssembly.instantiate;WebAssembly.instantiate=function(source,imports){return instantiate.call(this,source,patch(imports));};
 const streaming=WebAssembly.instantiateStreaming;WebAssembly.instantiateStreaming=function(source,imports){return streaming.call(this,source,patch(imports));};
 },{clock:Number(process.env.TH14_NATURAL_CLOCK??241224550)});page=await context.newPage();
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


 // Input path supplied explicitly by runner; bytes are held-mask source only.
 const input=await readFile(process.env.TH14_NATURAL_KEYS);const inputSha256=createHash('sha256').update(input).digest('hex');
 if(inputSha256!=='c48412a95f0fe9f685d97574e8ab0655d41e44ff9c41fda7bf788589b1b29c74')throw Error('Input identity differs');report.inputSha256=inputSha256;report.onlyHeldKeysAndDeclaredExternalClock=true;report.completionBoundaryUsed=false;report.rawStateWrites=false;
 const state=()=>page.evaluate(()=>{const w=document.querySelector('#gameFrame').contentWindow,m=w.Module;return{v:Array.from({length:39},(_,i)=>m._th14_acceptance_natural_state(i)),frame:w.core.th11_frame(),clock:w.__naturalClock,error:w.document.querySelector('#error')?.textContent};});
 await step('load-independent-held-mask-source',async()=>page.evaluate(data=>{const m=document.querySelector('#gameFrame').contentWindow.Module,p=m._malloc(data.length);try{m.HEAPU8.set(data,p);const rc=m._th14_acceptance_load_keys(p,data.length);if(rc!==1)throw Error('Input load rejected '+rc);return{accepted:true,bytes:data.length};}finally{m._free(p);}},Array.from(input)));
 await step('ordinary-real-menu-selection',async()=>{await cursor(1,0,'ArrowDown');await key('z');await cursor(5,1,'ArrowUp');await key('z');await cursor(6,0,'ArrowRight');await key('z');await cursor(7,1,'ArrowRight');return snapshot();});


 report.actualNativeRafLoop=true;report.recordedTapeInputApplied=true;report.fullNaturalCampaignAccepted=false;report.progress=[];report.stageImages=[];
 await key('z');await page.waitForFunction(()=>document.querySelector('#gameFrame')?.contentWindow?.Module?._th14_acceptance_natural_state(7)>=32,null,{timeout:90000});report.firstPlayerPrefix=await state();if(report.firstPlayerPrefix.v[28]<32)throw Error('Recorded held masks not sampled');
 report.firstSeedExpectedForOriginalTape=4607;report.firstSeedMatched=report.firstPlayerPrefix.v[8]===4607;report.referenceScoreEqualityClaimed=false;
 const factor=Number(process.env.TH14_NATURAL_FRAME_FACTOR??2);if(![1,2,8].includes(factor))throw Error('Unsupported display clock factor');
 await page.evaluate(factor=>{const m=document.querySelector('#gameFrame').contentWindow.Module,r=m.th14AsyncRuntime;const original=r.requestFrame;r.requestFrame=callback=>original(time=>callback(time*factor));},factor);report.hostDisplayClockFactor=factor;report.chromeRefreshUncapped=true;report.physicalRealtimePerformanceClaimed=false;report.gameplayStateNotRestored=true;
 const began=Date.now(),deadline=began+3300000;let lastProgress=0,endingSeen=false,staffStart=null,controlHeld=false,results=null;const captured=new Set();
 while(Date.now()<deadline){const f=await state();if(f.error||report.errors.length)throw Error('Runtime error '+JSON.stringify(f));if(f.v.slice(24,28).some(Boolean))throw Error('Non-ordinary mode '+JSON.stringify(f));
  if(f.v[7]>180000)throw Error('Bounded Player callback limit');
  if(f.v[0]===3){report.naturalGameOver=f;await page.screenshot({path:fileURLToPath(new URL('natural-game-over-private.png',out))});throw Error('Natural Game Over before full clear; reference seed '+report.firstSeedMatched);}
  if(f.v[0]===1&&f.v[4]&&!f.v[5]&&f.v[1]===f.v[6]&&f.v[3]>=240&&!captured.has(f.v[1])){
   const file='stage-'+f.v[1]+'-private.png',bytes=await page.screenshot({path:fileURLToPath(new URL(file,out))});report.stageImages.push({stage:f.v[1],state:f,sha256:createHash('sha256').update(bytes).digest('hex')});captured.add(f.v[1]);await save();
  }
  if(f.v[0]===5){endingSeen=true;if(f.v[14]!==2)throw Error('Unexpected ReimuB no-continue ending '+JSON.stringify(f));
   if(!f.v[35]&&f.v[34]){
    if(!f.v[13]&&!report.ending&&f.v[15]>=60&&f.v[33]){await page.screenshot({path:fileURLToPath(new URL('natural-ending-private.png',out))});report.ending=f;await save();}
    if(f.v[13]&&staffStart===null){staffStart=f.v[15];if(controlHeld){await page.keyboard.up('Control');controlHeld=false;}}
    if(f.v[13]&&!report.staff&&f.v[15]>=staffStart+600){await page.screenshot({path:fileURLToPath(new URL('natural-staff-private.png',out))});report.staff=f;await save();}
    if(report.ending&&(!f.v[13]||report.staff)){if(!controlHeld){await page.keyboard.down('Control');controlHeld=true;}await page.keyboard.down('z');await page.waitForTimeout(50);await page.keyboard.up('z');}
   }
  }
  if(endingSeen&&f.v[0]===0&&f.v[19]===14&&f.v[20]===2){results=f;break;}
  if(Date.now()-lastProgress>=10000){const q={seconds:(Date.now()-began)/1000,stage:f.v[1],phase:f.v[0],recordedFrames:f.v[3],callbacks:f.v[7],score:f.v[10]*10,lives:f.v[12]|0,reads:f.v[28],tails:f.v[29]};report.progress.push(q);await save();console.log(JSON.stringify(q));lastProgress=Date.now();}
  await page.waitForTimeout(200);
 }
 if(controlHeld)await page.keyboard.up('Control');await page.keyboard.up('z');
 if(!results||!report.ending||!report.staff||results.v[17]!==126||captured.size!==6)throw Error('Missing ordinary natural stage/ending/staff/results evidence');
 report.results=results;await page.waitForTimeout(1200);await page.screenshot({path:fileURLToPath(new URL('natural-results-private.png',out))});
 await step('native-results-and-replay-save-ui',async()=>{
  for(let i=0;i<12&&(await snapshot()).title[0]===14;i++)await key('z');await titleReady(15);await key('z');
  await page.waitForFunction(()=>{const c=document.querySelector('#gameFrame').contentWindow.core;return c.th11_title(0)===15&&c.th11_title(1)===3;},null,{timeout:15000});
  for(let i=0;i<12;i++){const t=(await snapshot()).title;if(t[0]!==15||t[1]!==3)break;await key('z');}await titleReady(15);
  return{menu:await snapshot(),viaActualKeys:true};
 });
 const files=()=>page.evaluate(()=>{const fs=document.querySelector('#gameFrame').contentWindow.Module.FS;
  const roots=fs.readdir('/save').filter(n=>/^(?:score.*\.dat|th14\.cfg)$/.test(n)).map(n=>'/save/'+n);
  const replays=fs.readdir('/save/replay').filter(n=>/^th14.*\.rpy$/.test(n)).map(n=>'/save/replay/'+n);
  return [...roots,...replays].map(path=>({name:path.split('/').at(-1),bytes:Array.from(fs.readFile(path))}));
 });
 const written=await files();report.savedFiles=[];for(const f of written){const b=Buffer.from(f.bytes);await writeFile(new URL('written-'+f.name+'-private.bin',out),b);report.savedFiles.push({name:f.name,bytes:b.length,sha256:createHash('sha256').update(b).digest('hex')});}
 if(!report.savedFiles.some(x=>/\.rpy$/.test(x.name)))throw Error('Native replay save did not write replay');
 await key('x');await titleReady(1);await key('Escape');await key('z');await page.waitForFunction(()=>!document.querySelector('#player')?.classList.contains('open'),null,{timeout:15000});report.normalExit=true;
 await page.reload({waitUntil:'networkidle'});await page.locator('#launch').click();const loadDeadline=Date.now()+120000;
 while(Date.now()<loadDeadline){const d=page.locator('#decisionDialog[open]:not(.closing)');if(await d.count())await d.locator('#decisionConfirm').click();if(await page.evaluate(()=>!!document.querySelector('#gameFrame')?.contentWindow?.core?.th11_phase))break;await page.waitForTimeout(200);}
 await page.locator('#gameFrame').click({position:{x:100,y:100}});await titleReady(1);
 const fresh=await files();report.freshFiles=[];for(const f of fresh){const b=Buffer.from(f.bytes);await writeFile(new URL('fresh-'+f.name+'-private.bin',out),b);report.freshFiles.push({name:f.name,bytes:b.length,sha256:createHash('sha256').update(b).digest('hex')});}
 for(const old of report.savedFiles.filter(x=>/\.rpy$/.test(x.name))){if(!report.freshFiles.some(x=>x.name===old.name&&x.sha256===old.sha256))throw Error('Fresh replay bytes not preserved');}
 report.scoreByteIdentityAcrossQuitAndReload=report.savedFiles.filter(x=>/^score/.test(x.name)).every(a=>report.freshFiles.some(b=>b.name===a.name&&b.sha256===a.sha256));
 report.freshTitleReady=await snapshot();await page.screenshot({path:fileURLToPath(new URL('natural-fresh-title-private.png',out))});await key('Escape');await key('z');await page.waitForFunction(()=>!document.querySelector('#player')?.classList.contains('open'),null,{timeout:15000});
 await Promise.all(pending);if(report.errors.length||report.captureErrors?.length)throw Error('Page or delivery errors');report.fullNaturalCampaignAccepted=true;report.passed=true;report.visualInspectionPending=true;report.semanticSaveQualificationPending=true;
}catch(e){report.failure=String(e.stack);if(page){report.failureUi=await page.evaluate(()=>({text:document.body.innerText.slice(-1800),frames:[...document.querySelectorAll('iframe')].map(e=>({src:e.src,error:e.contentWindow?.document.querySelector('#error')?.textContent,phase:e.contentWindow?.core?.th11_phase?.()}))})).catch(()=>null);await page.screenshot({path:fileURLToPath(new URL('failure-private.png',out))}).catch(()=>{});}process.exitCode=1;}finally{await save();await browser.close();console.log(JSON.stringify({passed:report.passed,prefix:report.firstPlayerPrefix,seedMatched:report.firstSeedMatched,normalExit:report.normalExit,fullNaturalCampaignAccepted:report.fullNaturalCampaignAccepted,progress:report.progress?.at(-1),failure:report.failure}));}
