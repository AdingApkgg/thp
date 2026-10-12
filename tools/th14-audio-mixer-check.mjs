import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/audio-mixer-check');mkdirSync(out,{recursive:true});const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'audio.wasm'),fixture='tests/cpp/th14-audio-mixer-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=14','-Itests/cpp/audio-shim',fixture,'cpp/sdl/AudioDevice.cpp','cpp/game/SoundEffects.cpp',...readdirSync(dir).filter(n=>n.endsWith('.o')&&n!=='cpp_game_SoundEffects.cpp.o').map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),musicDir=resolve(root,'runtimes/th14/th14_web/assets/sdl-native/music'),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{'/music':musicDir}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'),'utf8')),dat=readFileSync(target.dataArchives['th14.dat'].path),p=c.allocate(dat.length);new Uint8Array(c.memory.buffer,p,dat.length).set(dat);assert.equal(c.open_archive(p,dat.length),1);
const error=()=>{const b=new Uint8Array(c.memory.buffer),p=c.error();return new TextDecoder().decode(b.subarray(p,b.indexOf(0,p)));};
const mix=n=>{const p=c.mix(n);assert.ok(p,error());return new Float32Array(c.memory.buffer,p,n*2);};
const energy=n=>{let sum=0;while(n>0){const count=Math.min(1024,n),pcm=mix(count);for(const f of pcm){assert.ok(Number.isFinite(f));sum+=f*f;}n-=count;}return sum;};
const sounds=[];
for(let id=0;id<76;++id){c.stop_all();c.sound_start(id,0);const frames=c.sound_frames(id);assert.ok(frames>0);const prefix=energy(4096),body=energy(frames+2048);assert.ok(prefix+body>0,`sound ${id} PCM`);const tail=energy(4096),loop=(c.sound_flags(id)&1)!==0;assert.ok(loop?tail>0:tail===0,`sound ${id} tail ${tail},loop ${loop}`);c.stop_all();assert.equal(energy(4096),0,`sound ${id} stop`);sounds.push({id,frames,loop,prefixEnergy:prefix,bodyEnergy:body,tailEnergy:tail});}
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/music-fade-native.json'),'utf8')),fades=[];
for(const [n,row] of proof.rows.entries()){
 c.stop_all();assert.equal(c.music(0),1,error());c.master(row.master);c.fade(row.frames);const inverse=Math.fround(1-Math.fround(row.master/100));let db=row.master===0?-10000:Math.trunc(Math.fround(Math.fround(1-Math.fround(inverse*inverse))*5000))-5000;
 const gain=d=>Math.round(Math.fround(10**Math.fround(d/2000))*1000000);
 assert.ok(Math.abs((c.audio_stat(7)>>>0)-gain(db))<=1);
 for(const s of row.steps){c.update();for(const [kind,value] of s.events)if(kind==='volume')db=value|0;assert.ok(Math.abs((c.audio_stat(7)>>>0)-gain(db))<=1,`fade ${n} gain`);}
 assert.equal(energy(4096),0,`fade ${n} stopped PCM`);fades.push({master:row.master,frames:row.frames,finalDb:db,finalGain:c.audio_stat(7)>>>0});
}
const sha=b=>createHash('sha256').update(b).digest('hex');
const files=[fixture,'tests/cpp/th14-music-restore-fixture.cpp','tests/cpp/audio-shim/SDL3/SDL.h','cpp/sdl/AudioDevice.cpp','cpp/game/SoundEffects.cpp','cpp/game/SoundEffects.hpp','cpp/game/Th14AudioTables.inc','cpp/game/Th14MusicFade.hpp'];
writeFileSync(resolve(root,'docs/porting/th14-audio-mixer-verified.json'),JSON.stringify({passed:true,completeGame:false,nativeEquivalent:false,soundCases:sounds.length,fadeCases:fades.length,sounds,fades,wasmSha256:sha(bytes),archiveSha256:sha(dat),nativeExecutableSha256:proof.executableSha256,sourceHashes:Object.fromEntries(files.map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolSha256:sha(readFileSync(import.meta.filename)),scope:'Actual production AudioDevice and miniaudio with original 65 WAV resources: all 76 voices emit finite/nonzero PCM; ordinary voices stop after their actual resampled WAV length and voices20/55 continue looping; stopping each voice yields silence. Actual BGM fade update/retained gain versus 48 retail481540/481200 timelines, including zero/one frame, final PCM silence. SDL device stub, lossless FLAC BGM inputs (full original PCM comparison in separate report), no native DirectSound PCM, physical latency, asynchronous cadence or pause scheduling equivalence.'},null,2)+'\n');console.log(`PASS ${sounds.length} production PCM voices / ${fades.length} retail fade integration routes`);
