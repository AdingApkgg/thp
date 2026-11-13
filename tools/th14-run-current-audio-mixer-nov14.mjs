// Real C++ mixing into memory; the SDL boundary never reaches a hardware device.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {fullApplicationRecordingPlatform} from './th14-full-application-recording-platform-uniform2-nov13.mjs';

const R=resolve(import.meta.dirname,'..'),H=resolve(R,'artifacts/th14/current-audio-mixer-nov14');
const out=resolve(H,'run-loop-v3');assert.ok(!existsSync(out));mkdirSync(out);
const sha=b=>createHash('sha256').update(b).digest('hex'),load=p=>JSON.parse(readFileSync(p));
const component=resolve(H,'component-loop');
const build=load(resolve(component,'build.json')),bytes=readFileSync(resolve(component,'candidate.wasm'));
assert.equal(sha(bytes),build.outputs.candidate.wasmSha256);
for(const [name,digest]of Object.entries({...build.sourceBindingsByMode.candidate,...build.objectBindings}))assert.equal(sha(readFileSync(resolve(R,name))),digest,name);
const target=load(resolve(R,'runtimes/th14/target.json')),archivePath=target.dataArchives['th14.dat'].path;
const music=load(resolve(R,'artifacts/th14/published-vorbis-cache-nov13/prepared.json'));
const musicDirectory=resolve(R,music.musicDirectory);assert.ok(music.passed&&music.tracks===18);
for(const [name,digest]of Object.entries(music.sha256))assert.equal(sha(readFileSync(resolve(musicDirectory,name))),digest,name);
const module=new WebAssembly.Module(bytes),memory=new WebAssembly.Memory({initial:1024,maximum:16384,shared:true});
const errors=[];
const platform=fullApplicationRecordingPlatform(module,memory,{clockInput:1000000,archivePath,
 fontDirectory:resolve(R,'artifacts/th14/stable-stage-close-nov07/runtime-ready/fonts'),saveDirectory:out,
 onAsyncError:e=>errors.push(String(e?.stack??e))});
let virtualNs=0n;platform.env.SDL_GetTicksNS=()=>virtualNs;
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{'/music':musicDirectory}});
const instance=new WebAssembly.Instance(module,{env:platform.env,wasi_snapshot_preview1:wasi.wasiImport,
 wasi:{'thread-spawn':()=>{throw Error('Unexpected worker in the isolated mixer component');}}});
const c=instance.exports;platform.attach(c);wasi.initialize(instance);
const sounds=[],fades=[],musicCases=[],loopCases=[];let phase='initialize',exception=null,closed=false,totalMixedFrames=0;
const error=()=>{const data=new Uint8Array(memory.buffer),p=c.error();return new TextDecoder().decode(data.subarray(p,data.indexOf(0,p)));};
const energy=frames=>{
 let sum=0,peak=0;
 while(frames){const count=Math.min(1024,frames),p=c.mix(count);assert.ok(p,error());
  for(const f of new Float32Array(memory.buffer,p,count*2)){assert.ok(Number.isFinite(f)&&Math.abs(f)<=1);sum+=f*f;peak=Math.max(peak,Math.abs(f));}
  virtualNs+=BigInt(count)*1000000000n/44100n;totalMixedFrames+=count;frames-=count;
 }return {energy:sum,peak};
};
writeFileSync(resolve(out,'plan.json'),JSON.stringify({silent:true,hardwareDeviceOpened:false,realCppMixer:true,
 declaredSdlBoundary:true,virtualAudioClock:true,cachedOggTracks:18,newAssetsCopied:false,completeGame:false},null,2)+'\n');
try{
 const dat=readFileSync(archivePath),p=c.allocate(dat.length);assert.ok(p);
 new Uint8Array(memory.buffer,p,dat.length).set(dat);assert.equal(c.open_archive(p,dat.length),1,error());
 assert.equal(c.audio_stat(0),1);assert.equal(platform.summary().audibleOutput,false);
 phase='sfx';
 for(let id=0;id<76;++id){
  c.stop_all();c.sfx_master(100);c.sound_start(id,0);
  const frames=c.sound_frames(id);assert.ok(frames>0);const prefix=energy(4096),body=energy(frames+2048);
  assert.ok(prefix.energy+body.energy>0,`voice ${id}`);
  const tail=energy(4096),loop=!!(c.sound_flags(id)&1);assert.ok(loop?tail.energy>0:tail.energy===0,`voice ${id} tail`);
  c.stop_all();assert.equal(energy(4096).energy,0,`voice ${id} stop`);
  sounds.push({id,frames,loop,prefix,body,tail});
  if(id%16===15)console.log(JSON.stringify({phase,voices:sounds.length,totalMixedFrames}));
 }
 phase='sfx-pause';c.stop_all();c.sound_start(20,0);assert.ok(energy(4096).energy>0);
 c.sfx_pause(1);assert.equal(energy(4096).energy,0);c.sfx_pause(0);assert.ok(energy(4096).energy>0);c.stop_all();
 phase='music';
 for(const track of [0,1,17]){
  c.stop_all();c.master(100);c.mute(0);assert.equal(c.music(track),1,error());assert.equal(c.audio_stat(5),track);
  const firstSecond=energy(44100),normal=energy(3*44100);assert.ok(firstSecond.energy+normal.energy>0,`track ${track}`);
  const before=c.audio_stat(9);c.audio_pause(1);assert.equal(energy(4096).energy,0);assert.equal(c.audio_stat(9),before);
  c.audio_pause(0);assert.ok(energy(4*44100).energy>0);
  c.mute(1);assert.equal(energy(4096).energy,0);c.mute(0);assert.ok(energy(4*44100).energy>0);
  assert.equal(c.save(),1,error());assert.equal(c.music((track+1)%18),1,error());assert.ok(energy(4*44100).energy>0);
  assert.equal(c.restore(),1,error());assert.equal(c.audio_stat(5),track);assert.ok(energy(4*44100).energy>0);
  musicCases.push({track,firstSecond,normal,pausedCursorPreserved:true,muteZeroPcm:true,restoreTrackPreserved:true});
 }
 phase='fade';const native=load(resolve(R,'artifacts/th14/music-fade-native.json'));
 for(const [index,row]of native.rows.entries()){
  c.stop_all();c.mute(0);assert.equal(c.music(0),1,error());c.master(row.master);c.fade(row.frames);
  const inverse=Math.fround(1-Math.fround(row.master/100));
  let db=row.master===0?-10000:Math.trunc(Math.fround(Math.fround(1-Math.fround(inverse*inverse))*5000))-5000;
  const gain=d=>Math.round(Math.fround(10**Math.fround(d/2000))*1000000);
  assert.ok(Math.abs((c.audio_stat(7)>>>0)-gain(db))<=1,`fade ${index} initial`);
  for(const step of row.steps){c.update();for(const [kind,value]of step.events)if(kind==='volume')db=value|0;
   assert.ok(Math.abs((c.audio_stat(7)>>>0)-gain(db))<=1,`fade ${index} step`);}
  assert.equal(energy(4096).energy,0,`fade ${index} stopped PCM`);
  fades.push({master:row.master,frames:row.frames,finalDb:db});
 }
 phase='music-loops';
 for(let track=0;track<18;++track){
  c.stop_all();c.master(100);c.mute(0);assert.equal(c.music(track),1,error());
  const info=Array.from(new Uint32Array(memory.buffer,c.music_info(track),3));
  assert.equal(info[2],44100);assert.ok(info[0]>info[1]);
  const whole=energy(info[0]);assert.ok(whole.energy>0,`track ${track} whole`);
  const tail=energy(4*44100);assert.ok(tail.energy>0,`track ${track} loop tail`);
  const cursor=c.audio_stat(9);assert.ok(cursor>=info[1]&&cursor<info[0],`track ${track} cursor ${cursor}`);
  loopCases.push({track,totalFrames:info[0],loopStart:info[1],whole,tail,cursor});
  if(track%3===2)console.log(JSON.stringify({phase,tracks:loopCases.length,totalMixedFrames}));
 }
 assert.deepEqual(errors,[]);phase='complete';
}catch(e){exception=String(e?.stack??e);}
finally{
 try{c.audio_close();closed=true;await platform.closeServices();}catch(e){exception??=String(e?.stack??e);}
}
const summary=platform.summary();assert.equal(summary.audibleOutput,false);
const q={passed:phase==='complete'&&!exception,phase,exception,errors,closed,soundCases:sounds.length,sounds,
 musicCases,fades,fadeCases:fades.length,loopCases,loopCaseCount:loopCases.length,totalMixedFrames,silent:true,hardwareDeviceOpened:false,
 actualCurrentProviderObjects:145,oggTracksAvailable:18,virtualAudioClock:true,sdlDeliveryDeclared:true,
 sourceWasmSha256:sha(bytes),buildSha256:sha(readFileSync(resolve(component,'build.json'))),
 toolSha256:sha(readFileSync(import.meta.filename)),platform:summary,originalDirectSoundMixCompared:false,
 completeBrowserMixAccepted:false,gameLogicChanged:false,completeGame:false};
writeFileSync(resolve(out,'report.json'),JSON.stringify(q,null,2)+'\n');console.log(JSON.stringify({phase:q.phase,passed:q.passed,soundCases:q.soundCases,musicCases:q.musicCases.length,fadeCases:q.fadeCases,totalMixedFrames,exception}));
if(!q.passed)process.exitCode=1;
