import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/music-restore-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};nativePython('tools/th14-music-restore-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'music.wasm'),fixture='tests/cpp/th14-music-restore-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=14','-Itests/cpp/audio-shim',fixture,'cpp/sdl/AudioDevice.cpp',...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),musicDir=resolve(root,'runtimes/th14/th14_web/assets/sdl-native/music'),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{'/music':musicDir}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'),'utf8')),dat=readFileSync(target.dataArchives['th14.dat'].path),p=c.allocate(dat.length);new Uint8Array(c.memory.buffer,p,dat.length).set(dat);assert.equal(c.open_archive(p,dat.length),1);
const error=()=>{const b=new Uint8Array(c.memory.buffer),p=c.error();return new TextDecoder().decode(b.subarray(p,b.indexOf(0,p)));};
const sha=b=>createHash('sha256').update(b).digest('hex');const stat=n=>c.audio_stat(n)>>>0,cursor=()=>BigInt(stat(9))+(BigInt(stat(10))<<32n),savedCursor=()=>BigInt(stat(12))+(BigInt(stat(13))<<32n);
const mix=n=>{const p=c.mix(n);assert.ok(p,error());return Buffer.from(new Uint8Array(c.memory.buffer,p,n*8));};
const advance=n=>{while(n>0){const count=Math.min(1024,n);mix(count);n-=count;}};
const tracks=JSON.parse(readFileSync(resolve(root,'runtimes/th14/th14_web/assets/sdl-native/music-verification.json'),'utf8')),rows=[];
// Prefixes vary ordinary positions on every track; stage-one also crosses
// the actual loop end before saving its voice.
const scenarios=tracks.flatMap((_,track)=>[2048,32768].map(frames=>({track,frames})));
scenarios.push({track:1,frames:(Math.ceil(tracks.find(t=>t.name==='th14_02.wav').frames/1024)+8)*1024});
for(const {track,frames} of scenarios){
 assert.equal(c.audio_reset(),1,error());c.mute(0);assert.equal(c.music(track),1,error());advance(frames);const originalCursor=cursor(),expected=mix(1024);
 assert.equal(c.audio_reset(),1,error());assert.equal(c.music(track),1,error());advance(frames);assert.equal(cursor(),originalCursor);assert.equal(c.save(),1);assert.equal(savedCursor(),originalCursor);assert.equal(stat(11),track);
 assert.equal(c.music(17),1,error());advance(65536);assert.equal(savedCursor(),originalCursor,'result music must not advance the saved battle decoder');
 assert.equal(c.restore(),1);assert.equal(stat(5),track);assert.equal(stat(11),0xffffffff);assert.equal(cursor(),originalCursor,'restore retains the actual decoder cursor');
 const actual=mix(1024);assert.deepEqual(actual,expected,`PCM continuation ${track}/${frames}`);
 rows.push({track,frames,cursor:String(originalCursor),nextPcmSha256:sha(actual),resultMusicFrames:65536,passed:true});
}
assert.equal(c.music(2),1,error());advance(16384);c.audio_pause(1);const paused=cursor();assert.equal(c.save(),1);assert.equal(c.music(17),1,error());advance(4096);c.mute(1);assert.equal(c.restore(),1);assert.equal(cursor(),paused);assert.equal(stat(8),0);assert.equal(stat(7),0);assert.ok(mix(1024).every(b=>b===0),'muted restore stays silent');c.mute(0);
assert.equal(c.save(),1);c.discard();assert.equal(c.restore(),0);assert.equal(stat(11),0xffffffff);assert.equal(c.music(1),1,error());assert.equal(cursor(),0n,'retry uses a fresh position');
const native=JSON.parse(readFileSync(resolve(root,'artifacts/th14/music-restore-native.json'),'utf8'));
const files=[fixture,'tests/cpp/audio-shim/SDL3/SDL.h','cpp/sdl/AudioDevice.cpp','cpp/sdl/AudioDevice.hpp','cpp/sdl/Application.cpp','cpp/game/MusicCatalog.hpp'];
const report={passed:true,nativeCases:native.rows.length,losslessMusic:tracks.every(t=>t.lossless===true),pcmCases:rows.length,rows,pausedMuteDiscardRetry:true,nativeExecutableSha256:native.executableSha256,archiveSha256:sha(dat),wasmSha256:sha(bytes),scope:'Retail 449e6c..449ea5 captures active filename and double playback time; 44aef0..44af2c requests the saved filename then the identical time. Controlled music-thread/device boundaries. Production AudioDevice uses actual miniaudio/Vorbis decoding and original-resource music files: all 18 tracks at two nonzero prefixes plus a stage-one loop-boundary case, result music between save/restore, exact decoder cursor and bit-identical next 1,024 stereo float PCM frames against uninterrupted playback. Pause/mute, discard and retry also checked. SDL device is a deterministic stub; excludes physical/queued audio timing, full Application transition execution, native DirectSound PCM equality and lossless original music. Active FLAC files preserve original PCM; full original PCM comparison is a separate report.',musicFiles:Object.fromEntries(tracks.map(t=>[t.file,sha(readFileSync(resolve(musicDir,t.file)))])),sourceHashes:Object.fromEntries(files.map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-music-restore-native.py','tools/th14-music-restore-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-music-restore-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.nativeCases} retail music requests / ${report.pcmCases} exact PCM continuation cases.`);
