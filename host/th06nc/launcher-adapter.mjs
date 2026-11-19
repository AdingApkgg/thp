import {createKeyboardInputBridge} from './directory-keyboard.mjs';
import {createDirectInputBridge} from './host-direct-input-bridge.mjs';

const protocol='eagler-touhou/1',game='th06nc',origin=location.origin;
const query=new URLSearchParams(location.search),epoch=Number(query.get('runtimeEpoch'));
if(parent===window||!Number.isSafeInteger(epoch)||epoch<=0)throw Error('Open TH06nc from the Launcher');
const root='/savesth06nc',resources=new Map(),held=new Set();
let database,core,archive,index,configured=false,launched=false,configuration,firstFrame=false;
let touch={fireEnabled:false,focusEnabled:false,joystickX:0,joystickY:0},bombSerial=0,escapeSerial=0,pulses=new Set();
let frames=0,healthStart=performance.now(),previousFrame=healthStart,maxGap=0;
const contacts=new Map();let targetDelta=[0,0];
const overlay=document.createElement('canvas');overlay.width=1926;overlay.height=1080;overlay.style.cssText='position:absolute;inset:0;width:100%;height:100%;pointer-events:none';document.querySelector('main').append(overlay);const marker=overlay.getContext('2d');
const emit=(event,fields={})=>parent.postMessage({protocol,game,epoch,event,...fields},origin);
const reply=(message,fields)=>message.request&&parent.postMessage({protocol,game,epoch,request:message.request,...fields},origin);
const complete=tx=>new Promise((yes,no)=>{tx.oncomplete=yes;tx.onerror=tx.onabort=()=>no(tx.error||Error('Save transaction failed'));});
function filePath(path){if(typeof path!=='string')throw Error('Invalid save path');const relative=path.startsWith(root+'/')?path.slice(root.length+1):path;if(!/^(?:score\.dat|th06\.(?:cfg|env)|achievements\.json|last-name\.txt|score\.dat\.invalid|replay\/[a-zA-Z0-9_.-]+\.rpy)$/.test(relative))throw Error('Invalid save path');return root+'/'+relative;}
async function openDatabase(){
 if(database)return database;
 database=await new Promise((yes,no)=>{const request=indexedDB.open(root,21);request.onupgradeneeded=()=>{const store=request.result.createObjectStore('FILE_DATA');store.createIndex('timestamp','timestamp',{unique:false});for(const path of [root,root+'/replay'])store.put({mode:16877,timestamp:new Date()},path);};request.onsuccess=()=>yes(request.result);request.onerror=()=>no(request.error);});
 database.onversionchange=()=>database.close();return database;
}
const configFiles={gameConfig:'th06.cfg',environmentConfig:'th06.env',scoreFile:'score.dat',achievements:'achievements.json',lastName:'last-name.txt',scoreFileInvalidBackup:'score.dat.invalid'};
function requestView(request,convert){return {get result(){return convert(request.result);},get error(){return request.error;},set onsuccess(fn){request.onsuccess=fn;},set onerror(fn){request.onerror=fn;}};}
function configBytes(key,value){return key==='achievements'?new TextEncoder().encode(JSON.stringify(value)):key==='lastName'?new TextEncoder().encode(value):new Uint8Array(value).slice();}
function configValue(key,entry){if(!entry)return undefined;const bytes=entry.contents;return key==='achievements'?JSON.parse(new TextDecoder().decode(bytes)):key==='lastName'?new TextDecoder().decode(bytes):bytes.slice().buffer;}
// The original save codec uses this small store interface. Its only backing
// store is the same IDBFS FILE_DATA database read by Launcher file/cloud tools.
function saveDatabase(){return {transaction(names,mode){const tx=database.transaction('FILE_DATA',mode),store=tx.objectStore('FILE_DATA'),enqueue=operation=>{try{return operation();}catch(error){try{tx.abort();}catch{}throw error;}};return new Proxy(tx,{get(target,key){if(key==='objectStore')return name=>name==='config'?{
 get:key=>requestView(store.get(filePath(configFiles[key])),entry=>configValue(key,entry)),
 put:(value,key)=>enqueue(()=>store.put({mode:33188,timestamp:new Date(),contents:configBytes(key,value)},filePath(configFiles[key])))
 }:{getAll:()=>{const keys=store.getAllKeys();return requestView(store.getAll(),entries=>entries.map((entry,i)=>({...entry,path:keys.result[i].slice(root.length+1)})).filter(entry=>entry.path.startsWith('replay/')).map(entry=>({path:entry.path,data:entry.contents.slice().buffer})));},put:file=>enqueue(()=>store.put({mode:33188,timestamp:new Date(),contents:new Uint8Array(file.data),path:file.path},filePath(file.path)))};const value=Reflect.get(target,key,target);return typeof value==='function'?value.bind(target):value;},set(target,key,value){return Reflect.set(target,key,value,target);}});}};}
async function loadResource(resource){
 if(!resource||typeof resource.path!=='string'||typeof resource.url!=='string')throw Error('Invalid managed resource');
 const url=new URL(resource.url,location.href);if(url.origin!==origin)throw Error('Foreign resource');
 const response=await fetch(url);if(!response.ok)throw Error('Managed resource download failed');const bytes=new Uint8Array(await response.arrayBuffer());
 if(resource.bytes!=null&&resource.bytes!==bytes.length)throw Error('Resource length mismatch');
 if(resource.sha256){const hash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');if(hash!==resource.sha256)throw Error('Resource hash mismatch');}
 resources.set(resource.path,bytes);
}
async function prepareData(){
 if(archive)return;
 const result=await parent.__eaglerPrepareManagedRuntimeDataV1({game,generation:query.get('gameGeneration'),epoch});
 archive=new Uint8Array(result.buffer);const length=new DataView(archive.buffer).getUint32(0,true);
 if(length<2||length>1024*1024||length+4>archive.length)throw Error('Invalid TH06nc content header');
 const header=JSON.parse(new TextDecoder().decode(archive.subarray(4,length+4)));
 if(header.schema!=='th06nc/content/1')throw Error('Unsupported TH06nc content');
 index=new Map(header.files.map(file=>[file.path,{...file,offset:file.offset+length+4}]));
}
async function load(path){
 const music=path.match(/^\.\/artifacts\/audio\/(bgm2?)\/(th06_\d+)\.ogg$/);
 if(music){const key='/music/'+music[1]+'_'+music[2]+'.ogg';if(resources.has(key))return resources.get(key);throw Error('Music resource not installed: '+key);}
 const entry=index.get(path.replace(/^\.\/artifacts\//,''));if(!entry||entry.offset+entry.bytes>archive.length)throw Error('Missing installed asset: '+path);
 const stream=new Blob([archive.subarray(entry.offset,entry.offset+entry.bytes)]).stream().pipeThrough(new DecompressionStream('gzip'));
 const bytes=new Uint8Array(await new Response(stream).arrayBuffer());if(bytes.length!==entry.decodedBytes)throw Error('Damaged installed asset: '+path);return bytes;
}
const keyboard=createKeyboardInputBridge({protocol,game,epoch,origin,ready:()=>launched,dispatch:(event,down)=>{if(down){held.add(event.code);core?.held.add(event.code);}else{held.delete(event.code);core?.held.delete(event.code);}},reset:clear});
function clearTouch(){pulses.clear();contacts.clear();targetDelta=[0,0];touch={fireEnabled:false,focusEnabled:false,joystickX:0,joystickY:0};}
function clear(){held.clear();core?.held.clear();clearTouch();}
function input(message){
 if(message.command==='keyboard')return keyboard.submit(message)||false;
 if(message.command==='keyboard-clear'){keyboard.clear();held.clear();core?.held.clear();return true;}
 if(message.command==='touch-cancel'){clearTouch();return true;}
 if(['touch-controls','direct-touch'].includes(message.command)&&configuration?.options?.touchEnabled!==true){clearTouch();return true;}
 if(message.command==='direct-touch'){
  if(!Number.isInteger(message.id)||!Number.isFinite(message.x)||!Number.isFinite(message.y)||!['down','move','up'].includes(message.type))return false;
  const previous=contacts.get(message.id);
  if(message.type==='down')contacts.set(message.id,{x:message.x,y:message.y});
  else if(message.type==='up'){contacts.delete(message.id);if(!contacts.size)targetDelta=[0,0];}
  else if(previous){if(contacts.keys().next().value===message.id){const sensitivity=Math.max(10,Math.min(300,configuration?.options?.touchSensitivity??150))/100;targetDelta[0]+=(message.x-previous.x)*856*sensitivity;targetDelta[1]+=(message.y-previous.y)*480*sensitivity;}contacts.set(message.id,{x:message.x,y:message.y});}
  return true;
 }
 if(message.command==='touch-controls'){
  if(![message.joystickX,message.joystickY,message.touchSensitivity].every(Number.isFinite))return false;
  touch=message;if(message.bombSerial!==bombSerial){bombSerial=message.bombSerial;pulses.add('KeyX');}if(message.escapeSerial!==escapeSerial){escapeSerial=message.escapeSerial;pulses.add('Escape');}return true;
 }
 return false;
}
globalThis.__eaglerDirectInputBridge=createDirectInputBridge({protocol,game,epoch,origin,ready:()=>launched,dispatch:input});
globalThis.th06ncHost={load,openSaveDatabase:async()=>{await openDatabase();return saveDatabase();},
 configureAudio(audio){for(const [name,option]of [['musicOutput','bgmVolume'],['sfxOutput','sfxVolume']]){const gain=audio.context.createGain();gain.gain.value=Math.max(0,Math.min(100,configuration?.options?.[option]??100))/100;gain.connect(audio.context.destination);audio[name]=gain;}},
 attach(value){core=value;},sample(){
  const keys=new Set(held),bits=globalThis.__eaglerGamepadInputBridge.sample(0);
  ['KeyZ','KeyX','ShiftLeft','Escape','ArrowUp','ArrowDown','ArrowLeft','ArrowRight','ControlLeft','Enter','KeyZ','KeyR'].forEach((code,i)=>{if(bits>=0&&(bits&(1<<i)))keys.add(code);});
  if(touch.fireEnabled&&core?.player())keys.add('KeyZ');if(touch.focusEnabled)keys.add('ShiftLeft');
  if(contacts.size>=2&&configuration?.options?.touchFocusMode==='two-finger')keys.add('ShiftLeft');
  if(touch.joystickX>6553)keys.add('ArrowRight');if(touch.joystickX< -6553)keys.add('ArrowLeft');if(touch.joystickY>6553)keys.add('ArrowDown');if(touch.joystickY< -6553)keys.add('ArrowUp');
  const player=core?.player();if(player&&[0,3].includes(player.state)){
   const focused=keys.has('ShiftLeft'),speed=player.v.getFloat32(focused?0x7864:0x7860,true),diagonal=player.v.getFloat32(focused?0x786c:0x7868,true);
   const x=Math.abs(targetDelta[0])>=speed/2,y=Math.abs(targetDelta[1])>=speed/2,amount=x&&y?diagonal:speed;
   if(x){keys.add(targetDelta[0]>0?'ArrowRight':'ArrowLeft');targetDelta[0]-=Math.sign(targetDelta[0])*amount;}if(y){keys.add(targetDelta[1]>0?'ArrowDown':'ArrowUp');targetDelta[1]-=Math.sign(targetDelta[1])*amount;}
  }
  for(const code of pulses)keys.add(code);pulses.clear();return keys;
 },draw(stage,phase){marker.clearRect(0,0,1926,1080);if(!configuration?.options?.alwaysHitbox||!stage||!['game','paused','game-over','game-result-transition'].includes(phase)||![0,3].includes(stage.player.state))return;const player=stage.player,[x,y]=player.position,scale=1080/480,viewport=core.viewport();marker.beginPath();marker.arc((viewport.x+x)*scale,(viewport.y+y)*scale,Math.max(1.5,player.hitRadius)*scale,0,Math.PI*2);marker.fillStyle='#e92842';marker.fill();marker.lineWidth=scale*.65;marker.strokeStyle='#fff';marker.stroke();},
 firstFrame(){const now=performance.now();maxGap=Math.max(maxGap,now-previousFrame);previousFrame=now;frames++;if(!firstFrame){firstFrame=true;emit('first-frame');emit('runtime-info',{renderer:'WebGL2',architecture:'JavaScript',version:'TH06nc browser'});}},exit(){clear();emit('exit',{code:0,status:'success'});},error(error){emit('error',{message:String(error?.message??error)});},music:()=>configuration?.music??'none'};
async function files(message){
 const path=['read','write','remove'].includes(message.command)?filePath(message.path):null;let bytes;
 if(message.command==='write'){
  const input=message.bytes;if(!Array.isArray(input)||input.length>4*1024*1024)throw Error('Invalid file bytes');
  for(let i=0;i<input.length;i++)if(!Object.hasOwn(input,i)||!Number.isInteger(input[i])||input[i]<0||input[i]>255)throw Error('Invalid file bytes');bytes=Uint8Array.from(input);
 }
 if(['sync','write','remove'].includes(message.command)&&core)await core.flush();
 await openDatabase();const tx=database.transaction('FILE_DATA',['write','remove'].includes(message.command)?'readwrite':'readonly'),store=tx.objectStore('FILE_DATA');let request;
 if(message.command==='list'){request=store.getAll();var paths=store.getAllKeys();}else if(message.command==='read')request=store.get(path);
 else if(message.command==='write'){
  request=store.put({mode:33188,timestamp:new Date(),contents:bytes,...(path.includes('/replay/')?{path:path.slice(root.length+1)}:{})},path);
 }else if(message.command==='remove')request=store.delete(path);
 await complete(tx);
 if(message.command==='list')return {files:request.result.map((entry,i)=>({path:paths.result[i].slice(root.length+1),size:entry.contents?.length??0,modifiedAt:Number(entry.timestamp),mode:entry.mode})).filter(entry=>(entry.mode&0xf000)===0x8000)};
 if(message.command==='read'){if(!request.result)throw Object.assign(Error('File not found'),{errno:44});return {bytes:[...request.result.contents]};}
 if(core&&['write','remove'].includes(message.command)){const fresh=new core.saves.constructor();await fresh.open();if(filePath(message.path).startsWith(root+'/replay/')){core.saves.replays=fresh.replays;core.saves.invalid=[...core.saves.invalid.filter(entry=>!entry.path.startsWith('replay/')),...fresh.invalid.filter(entry=>entry.path.startsWith('replay/'))];}else{const rng=core.saves.saveRng;Object.assign(core.saves,fresh);core.saves.saveRng=rng;}}return {};
}
addEventListener('message',async event=>{
 const message=event.data;if(event.source!==parent||event.origin!==origin||!message||message.protocol!==protocol||message.game!==game||message.epoch!==epoch)return;
 try{
  let result={};
  if(message.command==='configure'){
   if(launched)throw Error('Runtime already launched');if(!['ogg','none'].includes(message.music))throw Error('Unsupported music mode');configuration=message;
   for(const resource of [...(message.resources??[]),...(message.runtimeResources??[]),...(message.sharedResources??[])])await loadResource(resource);
   configured=true;
  }else if(message.command==='resources'){for(const resource of message.resources??[])await loadResource(resource);}
  else if(message.command==='launch'){
   if(!configured||launched)throw Error('Invalid launch phase');await prepareData();launched=true;await import('./game.mjs');await core.boot;
  }else if(['list','read','write','remove','sync'].includes(message.command))result=await files(message);
  else if(!input(message))throw Error('Unsupported Runtime command: '+message.command);
  reply(message,{ok:true,...result});
 }catch(error){reply(message,{ok:false,error:String(error.message),...(error.errno?{errno:error.errno}:{})});if(message.command==='launch')emit('error',{message:String(error.stack??error)});}
});
addEventListener('keydown',event=>{if(keyboard.event(event,true)){core?.audio.unlock().catch(()=>{});event.preventDefault();}},true);
addEventListener('keyup',event=>{if(keyboard.event(event,false))event.preventDefault();},true);
for(const type of ['blur','pagehide'])addEventListener(type,()=>{keyboard.clear();clear();});
document.addEventListener('visibilitychange',()=>{if(document.hidden){keyboard.clear();clear();core?.pause();core?.audio.context.suspend();}else if(launched)core?.audio.unlock().catch(()=>{});});
setInterval(()=>{if(!firstFrame)return;const now=performance.now();emit('frame-health',{fps:frames*1000/(now-healthStart),maxGapMs:maxGap});frames=0;maxGap=0;healthStart=now;emit('audio-health',{backend:'webaudio',robust:true,underruns:0,queuedMs:0,state:core?.audio.context.state});},2000);
await openDatabase();emit('ready',{saveRoot:root});
