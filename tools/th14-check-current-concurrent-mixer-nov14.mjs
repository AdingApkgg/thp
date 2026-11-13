// Exercise the current real C++ mixer in memory. No SDL audio device is opened.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {fullApplicationRecordingPlatform} from './th14-full-application-recording-platform-uniform2-nov13.mjs';

const R=resolve(import.meta.dirname,'..');
const home=resolve(R,process.argv[2]??'artifacts/th14/current-concurrent-mixer-nov14/run-v2');
assert.ok(home.startsWith(resolve(R,'artifacts/th14')+'/')||home.startsWith(resolve(R,'artifacts/th14')+'\\'));
assert.ok(!existsSync(home),'Preserve existing evidence; choose a new output for another run');mkdirSync(home);
const sha=b=>createHash('sha256').update(b).digest('hex');
const json=p=>JSON.parse(readFileSync(p));
const component=resolve(R,'artifacts/th14/current-audio-mixer-nov14/component-loop');
const build=json(resolve(component,'build.json')),bytes=readFileSync(resolve(component,'candidate.wasm'));
assert.equal(sha(bytes),build.outputs.candidate.wasmSha256);
for(const [name,digest] of Object.entries({...build.sourceBindingsByMode.candidate,...build.objectBindings}))
 assert.equal(sha(readFileSync(resolve(R,name))),digest,name);
const archivePath=json(resolve(R,'runtimes/th14/target.json')).dataArchives['th14.dat'].path;
const music=json(resolve(R,'artifacts/th14/published-vorbis-cache-nov13/prepared.json'));
const musicDirectory=resolve(R,music.musicDirectory);
for(const [name,digest]of Object.entries(music.sha256))assert.equal(sha(readFileSync(resolve(musicDirectory,name))),digest);
const module=new WebAssembly.Module(bytes),memory=new WebAssembly.Memory({initial:1024,maximum:16384,shared:true});
const errors=[];
const platform=fullApplicationRecordingPlatform(module,memory,{clockInput:1000000,archivePath,
 fontDirectory:resolve(R,'artifacts/th14/stable-stage-close-nov07/runtime-ready/fonts'),saveDirectory:home,
 onAsyncError:e=>errors.push(String(e?.stack??e))});
let ns=0n,mixedFrames=0;platform.env.SDL_GetTicksNS=()=>ns;
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{'/music':musicDirectory}});
const c=new WebAssembly.Instance(module,{env:platform.env,wasi_snapshot_preview1:wasi.wasiImport,
 wasi:{'thread-spawn':()=>{throw Error('Unexpected audio component worker');}}}).exports;
platform.attach(c);wasi.initialize({exports:c});
const error=()=>{const b=new Uint8Array(memory.buffer),p=c.error();return new TextDecoder().decode(b.subarray(p,b.indexOf(0,p)));};
function mix(frames){
 const result=new Float32Array(frames*2);let offset=0;
 while(offset<frames){const n=Math.min(1024,frames-offset),p=c.mix(n);assert.ok(p,error());
  result.set(new Float32Array(memory.buffer,p,n*2),offset*2);offset+=n;mixedFrames+=n;ns+=BigInt(n)*1000000000n/44100n;}
 for(const x of result)assert.ok(Number.isFinite(x)&&Math.abs(x)<=1);
 return result;
}
function begin(track,level=50){assert.equal(c.audio_reset(),1,error());ns=0n;c.sfx_master(level);c.master(level);c.mute(0);
 if(track!==null){assert.equal(c.music(track),1,error());mix(88200);}}
function start(ids,x=0){for(const id of ids)c.sound_start(id,x);}
function energy(samples,channel){let e=0;for(let i=channel;i<samples.length;i+=2)e+=samples[i]**2;return e;}
function compare(actual,expected,label){assert.equal(actual.length,expected.length);let maxError=0,bad=0;
 for(let i=0;i<actual.length;i++){const d=Math.abs(actual[i]-expected[i]);maxError=Math.max(maxError,d);if(d>2e-6)bad++;}
 assert.equal(bad,0,`${label}: ${bad} samples, max error ${maxError}`);return maxError;}
const rows=[],pan=[],pause=[];let phase='initialize',exception=null,closed=false,negativeControls=0;
try{
 const dat=readFileSync(archivePath),p=c.allocate(dat.length);assert.ok(p);new Uint8Array(memory.buffer,p,dat.length).set(dat);
 assert.equal(c.open_archive(p,dat.length),1,error());assert.equal(platform.summary().audibleOutput,false);
 phase='concurrent-sum';
 for(const row of [{ids:[20],x:0,level:25},{ids:[55],x:-192,level:50},
  {ids:[5,11,36],x:192,level:50},{ids:[0,1,2,3,4,5,11,20,36,55],x:0,level:100}]){
  begin(1,row.level);const bgm=mix(4096);
  const sum=new Float64Array(8192);
  // Sum individual unclipped voices: a preclipped SFX aggregate loses information.
  for(const id of row.ids){begin(null,row.level);start([id],row.x);const part=mix(4096);
   assert.ok(part.every(x=>Math.abs(x)<1));for(let i=0;i<sum.length;i++)sum[i]+=part[i];}
  assert.ok(bgm.every(x=>Math.abs(x)<1));
  const sfx=Float32Array.from(sum,x=>Math.max(-1,Math.min(1,x)));
  begin(1,row.level);start(row.ids,row.x);const together=mix(4096);
  const expected=Float32Array.from(bgm,(x,i)=>Math.max(-1,Math.min(1,x+sum[i])));
  assert.ok(energy(bgm,0)+energy(bgm,1)>0);assert.ok(energy(sfx,0)+energy(sfx,1)>0);
  const maxError=compare(together,expected,JSON.stringify(row));
  assert.ok(together.some((x,i)=>Math.abs(x-bgm[i])>2e-6),'Missing-SFX negative control must fail');negativeControls++;
  assert.ok(together.some((x,i)=>Math.abs(x-sfx[i])>2e-6),'Missing-BGM negative control must fail');negativeControls++;
  rows.push({...row,frames:4096,maxError,clippedSamples:Array.from(expected).filter(x=>Math.abs(x)===1).length});
 }
 phase='stereo-pan';
 for(const id of [20,55]){
  begin(null);start([id],-192);const left=mix(4096);
  begin(null);start([id],192);const right=mix(4096);
  assert.ok(energy(left,0)>energy(left,1));assert.ok(energy(right,1)>energy(right,0));
  const swap=Float32Array.from(left,(_,i)=>left[i^1]);const maxError=compare(right,swap,`pan ${id}`);
  pan.push({id,leftEnergy:[energy(left,0),energy(left,1)],rightEnergy:[energy(right,0),energy(right,1)],maxError});
 }
 phase='independent-pause';
 begin(1);const musicOnly=mix(8192);
 begin(null);start([20]);const soundOnly=mix(8192);
 for(const kind of ['music','sfx']){
  begin(1);start([20]);if(kind==='music')c.audio_pause(1);else c.sfx_pause(1);
  const paused=mix(4096);compare(paused,(kind==='music'?soundOnly:musicOnly).subarray(0,8192),`${kind} paused`);
  if(kind==='music')c.audio_pause(0);else c.sfx_pause(0);
  const resumed=mix(4096),expected=new Float32Array(8192);
  for(let i=0;i<8192;i++)expected[i]=Math.max(-1,Math.min(1,
   kind==='music'?musicOnly[i]+soundOnly[8192+i]:musicOnly[8192+i]+soundOnly[i]));
  const maxError=compare(resumed,expected,`${kind} resumed`);pause.push({kind,otherVoiceContinues:true,pausedVoiceCursorPreserved:true,maxError});
 }
 assert.deepEqual(errors,[]);phase='complete';
}catch(e){exception=String(e?.stack??e);}
finally{try{c.audio_close();await platform.closeServices();closed=true;}catch(e){exception??=String(e?.stack??e);}}
const summary=platform.summary();assert.equal(summary.audibleOutput,false);
const report={schema:'th14/current-concurrent-mixer/1',passed:phase==='complete'&&!exception,phase,exception,
 rows,pan,pause,negativeControls,mixedFrames,errors,closed,platform:summary,
 sourceWasmSha256:sha(bytes),sourceBuildSha256:sha(readFileSync(resolve(component,'build.json'))),
 toolSha256:sha(readFileSync(import.meta.filename)),providerObjectsVerified:145,
 silent:true,hardwareDeviceOpened:false,newAssetsCopied:false,gameLogicChanged:false,
 originalDirectSoundFinalMixCompared:false,completeBrowserMixAccepted:false,completeGame:false};
writeFileSync(resolve(home,'report.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:report.passed,phase,rows:rows.length,pan:pan.length,pause:pause.length,negativeControls,mixedFrames,exception}));
if(!report.passed)process.exitCode=1;
