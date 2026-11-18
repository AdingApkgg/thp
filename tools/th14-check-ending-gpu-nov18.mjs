import {chromium} from 'playwright-core';
import {mkdir,writeFile,readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
const option=(name,fallback)=>process.argv.find(a=>a.startsWith('--'+name+'='))?.slice(name.length+3)??fallback;
const base=option('url',process.env.TH14_FULL_REPLAY_BASE??'http://localhost:8257/?game=th14');
const out=new URL('./'+option('output',process.env.TH14_FULL_REPLAY_OUTPUT??'../artifacts/th14/ending-gpu-private-nov18')+'/',import.meta.url);await mkdir(out,{recursive:false});
const report={schema:'th14/launcher-normal/1',startedAt:new Date().toISOString(),url:base,scope:'Fresh isolated headless Chrome; actual packaged launcher UI, no existing user browser',steps:[],errors:[],consoleErrors:[],httpErrors:[],delivery:[],passed:false};
const source=await readFile(new URL(import.meta.url));report.harnessSha256=createHash('sha256').update(source).digest('hex');await writeFile(new URL('harness.mjs',out),source);
const save=()=>writeFile(new URL('report.json',out),JSON.stringify(report,null,2));
const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',args:['--enable-gpu','--use-gl=angle','--use-angle=d3d11','--mute-audio']});let page;
try{
 report.browser=browser.version();const context=await browser.newContext({viewport:{width:1280,height:900}});page=await context.newPage();
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

 const flow=()=>page.evaluate(()=>{const w=document.querySelector('#gameFrame').contentWindow;return {v:Array.from({length:26},(_,i)=>w.Module._th14_acceptance_flow(i)),frame:w.core.th11_frame(),title:[0,1,2].map(k=>w.core.th11_title(k)),error:w.document.querySelector('#error')?.textContent};});
 const complete=()=>page.evaluate(()=>document.querySelector('#gameFrame').contentWindow.Module._th14_acceptance_complete_boundary());
 if(await complete()!==-1)throw Error('Title guard failed');
 report.privateCompletionBoundaryProbe=true;report.naturalCampaignClaimed=false;report.cases=[];
 for(const [character,name]of [[0,'reimu'],[1,'marisa'],[2,'sakuya']])for(const shot of [0,1]){
  await step(name+'-'+shot+'-ending-staff-gpu',async()=>{
   await titleReady(1);await cursor(1,0,'ArrowDown');await key('z');await cursor(5,1,'ArrowUp');await key('z');await cursor(6,character,'ArrowRight');await key('z');await cursor(7,shot,'ArrowRight');await key('z');
   const result={character,shot,transitions:[],ending:null,staff:null,results:null,privateCompletionEvent:true,naturalCampaignClaimed:false};report.cases.push(result);
   let deadline=Date.now()+180000;
   while(Date.now()<deadline){const f=await flow();if(f.error)throw Error(f.error);if(f.v[0]===5)break;
    if(f.v[0]===1&&f.v[2]===1&&!f.v[3]&&f.v[1]===f.v[4]&&f.v[1]===f.v[15]&&f.frame>8&&!result.transitions.some(t=>t.before.v[1]===f.v[1])){
     if(f.v[9]!==character||f.v[10]!==shot||f.v.slice(16,20).some(Boolean))throw Error('Selection or mode guard '+JSON.stringify(f));
     const rc=await complete();result.transitions.push({before:f,returnCode:rc});if(rc!==1)throw Error('Completion boundary rejected '+rc);console.log(name+shot+' stage '+f.v[1]);await save();
    }await page.waitForTimeout(100);
   }
   if(result.transitions.map(t=>t.before.v[1]).join(',')!=='1,2,3,4,5,6')throw Error('Missing transitions '+JSON.stringify(result));
   deadline=Date.now()+300000;let lastProgress=0,staffStart=null,held=false;
   while(Date.now()<deadline){const f=await flow();if(f.error)throw Error(f.error);
    if(f.v[0]===0&&f.v[8]===14){result.results=f;break;}
    if(f.v[0]===5&&f.v[6]&&!f.v[7]){
     if(!f.v[25]&&!result.ending&&f.v[14]>=60&&(f.v[23]>0||f.v[13]>0)){
      await page.screenshot({path:fileURLToPath(new URL(name+'-'+shot+'-ending-private.png',out))});result.ending=f;await save();
     }
     if(f.v[25]&&staffStart===null){staffStart=f.v[14];if(held){await page.keyboard.up('Control');held=false;}}
     if(f.v[25]&&!result.staff&&f.v[14]>=staffStart+600){await page.screenshot({path:fileURLToPath(new URL(name+'-'+shot+'-staff-private.png',out))});result.staff=f;await save();}
     if(result.ending&&(!f.v[25]||result.staff)){
      if(!held){await page.keyboard.down('Control');held=true;}
      await page.keyboard.down('z');await page.waitForTimeout(35);await page.keyboard.up('z');
     }
    }
    if(Date.now()-lastProgress>5000){console.log(name+shot+' flow '+JSON.stringify(f));lastProgress=Date.now();}
    await page.waitForTimeout(100);
   }
   if(held)await page.keyboard.up('Control');await page.keyboard.up('z');
   if(!result.ending||!result.staff||!result.results)throw Error('Ending/staff/results not all observed '+JSON.stringify(result));
   await titleReady(14);await page.waitForTimeout(1200);result.resultsReady=await flow();await page.screenshot({path:fileURLToPath(new URL(name+'-'+shot+'-results-private.png',out))});
   for(let i=0;i<12&&(await snapshot()).title[0]===14;i++)await key('z');await titleReady(15);await key('x');await titleReady(1);result.returnedToMain=true;result.visualInspectionPending=true;return result;
  });
 }
 await step('native-quit-after-six',async()=>{await key('Escape');await key('z');await page.waitForFunction(()=>!document.querySelector('#player')?.classList.contains('open'),null,{timeout:15000});return{closed:true};});
 await Promise.all(pending);report.deliveryComplete=report.delivery.some(r=>r.url.endsWith('th14-sdl.wasm'));
 if(!report.deliveryComplete||report.errors.length||report.captureErrors?.length)throw Error('Runtime delivery or page errors failed');
 report.passed=true;
}catch(e){report.failure=String(e.stack);if(page){report.failureUi=await page.evaluate(()=>({text:document.body.innerText.slice(-4500),frames:[...document.querySelectorAll('iframe')].map(e=>({src:e.src,error:e.contentWindow?.document.querySelector('#error')?.textContent,phase:e.contentWindow?.core?.th11_phase?.()}))})).catch(()=>null);await page.screenshot({path:fileURLToPath(new URL('failure-private.png',out))}).catch(()=>{});}process.exitCode=1;}finally{await save();await browser.close();console.log(JSON.stringify({passed:report.passed,steps:report.steps,errors:report.errors,consoleErrors:report.consoleErrors,httpErrors:report.httpErrors,failure:report.failure,failureUi:report.failureUi}));}
