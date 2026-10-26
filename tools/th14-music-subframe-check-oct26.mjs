// Silent production mixer comparison against whole retail restore/refill buffers.
import assert from 'node:assert/strict';
import {readFileSync as read,writeFileSync as write,mkdirSync as mkdir,existsSync as exists,openSync,readSync,closeSync} from 'node:fs';
import {resolve,relative} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),sha=b=>createHash('sha256').update(b).digest('hex');
const opts=new Map();for(let n=2;n<process.argv.length;n+=2){assert(['--output','--source','--native'].includes(process.argv[n]));assert(!opts.has(process.argv[n]));opts.set(process.argv[n],process.argv[n+1]);}
assert(opts.has('--output')&&opts.has('--source')&&opts.has('--native'));
const out=resolve(root,opts.get('--output')),source=resolve(root,opts.get('--source')),nativePath=resolve(root,opts.get('--native'));
assert(relative(resolve(root,'artifacts/th14'),out)&&!relative(resolve(root,'artifacts/th14'),out).startsWith('..'));assert(!exists(resolve(out,'comparison.json')));mkdir(out,{recursive:true});
const bindings={},bind=p=>{const b=read(p);bindings[relative(root,p).replaceAll('\\','/')]={bytes:b.length,sha256:sha(b)};return b;};
const corePath=resolve(root,'artifacts/th14/stage-item-retirement-oct25/curve-origin-observer-oct26/observer-build.json'),core=JSON.parse(bind(corePath));
assert(core.compiled&&core.objectBindings.length===141);for(const row of core.objectBindings)assert.equal(sha(bind(row.path)),row.sha256);
const shimPath=resolve(root,'runtimes/th12/th12_web/tests/cpp/audio-shim/SDL3/SDL.h');
const shim=bind(shimPath).toString().replace('inline std::uint64_t SDL_GetTicksNS(){return 0;}','inline std::uint64_t th14_test_clock_ns=0;\ninline std::uint64_t SDL_GetTicksNS(){return th14_test_clock_ns;}');
mkdir(resolve(out,'shim/SDL3'),{recursive:true});write(resolve(out,'shim/SDL3/SDL.h'),shim);
const header=resolve(root,'runtimes/th12/th12_web/cpp/sdl/AudioDevice.hpp').replaceAll('\\','/');
const fixturePath=resolve(root,'runtimes/th12/th12_web/tests/cpp/th14-music-restore-fixture.cpp');
write(resolve(out,'fixture.cpp'),bind(fixturePath).toString().replace('../../cpp/sdl/AudioDevice.hpp',header)+'\nAPI(clock_ns) void clock_ns(unsigned long long ns){th14_test_clock_ns=ns;}\nAPI(audio_suspend) void audio_suspend(int on){audio.suspend(on!=0);}\n');
const compiler=resolve(root,'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),wasmPath=resolve(out,'probe.wasm');bind(compiler);bind(source);bind(import.meta.filename);
const flags=['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-ffp-contract=off','-fno-strict-aliasing','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-I'+resolve(out,'shim')];
try{execFileSync(compiler,[...flags,resolve(out,'fixture.cpp'),source,...core.objectBindings.map(r=>r.path),'-o',wasmPath],{cwd:root,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out},windowsHide:true,stdio:'pipe'});}catch(error){write(resolve(out,'compile-error.txt'),error.stderr??String(error));throw Error('Compilation failed: '+resolve(out,'compile-error.txt'));}
bind(resolve(out,'fixture.cpp'));bind(resolve(out,'shim/SDL3/SDL.h'));
// Bind all current includes used by this translation unit, independently of the
// retained game objects; no unrelated working tree object is substituted.
const deps=execFileSync(compiler,[...flags.filter(f=>!f.startsWith('-Wl,')&&f!=='-mexec-model=reactor'),'-MM',source],{cwd:root,windowsHide:true,encoding:'utf8'}).replace(/\\\r?\n/g,' ').split(/\s+/).slice(1).filter(Boolean);
for(const p of deps)bind(resolve(root,p));
const native=JSON.parse(bind(nativePath));assert.equal(native.cases,108);assert.equal(native.streamingCases,18);assert(native.fileServices.startsWith('Actual Windows readonly'));assert.equal(native.toolSha256,sha(bind(resolve(root,'tools/th14-music-subframe-native-oct26.py'))));assert.equal(native.executableSha256,'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353');
const target=JSON.parse(read(resolve(root,'runtimes/th14/target.json'))),archive=read(target.dataArchives['th14.dat'].path),bgm=openSync(target.dataArchives['thbgm.dat'].path,'r');
const musicDir=resolve(root,'runtimes/th14/th14_web/assets/sdl-native/music');
const bytes=bind(wasmPath),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{'/music':musicDir}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const p=c.allocate(archive.length);new Uint8Array(c.memory.buffer,p,archive.length).set(archive);assert.equal(c.open_archive(p,archive.length),1);
const error=()=>{const a=new Uint8Array(c.memory.buffer),at=c.error();return new TextDecoder().decode(a.subarray(at,a.indexOf(0,at)));};
const mix=count=>{const p=c.mix(count);assert.ok(p,error());return Buffer.from(new Uint8Array(c.memory.buffer,p,count*8));};
const catalog=bind(resolve(root,'runtimes/th12/th12_web/cpp/game/MusicCatalog.hpp')).toString().match(/th14_music_tracks\[\]=\{([\s\S]*?)\};/)[1];const cues=new Map([...catalog.matchAll(/\{(\d+),"([^"]+)"\}/g)].map(m=>[m[2]+'.wav',Number(m[1])]));assert.equal(cues.size,18);
const cue=track=>{const name=native.rows.find(r=>r.track===track).name;assert(cues.has(name));return cues.get(name);};
function reset(track){c.clock_ns(0n);assert.equal(c.audio_reset(),1,error());c.mute(0);assert.equal(c.music(cue(track)),1,error());}
function rawChunk(chunk){const raw=Buffer.alloc(chunk.fill.bytes);let at=0;for(const call of chunk.reads){assert(call.bytes<=call.requested&&at+call.bytes<=raw.length);const n=readSync(bgm,raw,at,call.bytes,call.offset);assert.equal(n,call.bytes);assert.equal(sha(raw.subarray(at,at+n)),call.sha256);at+=n;}assert.equal(sha(raw),chunk.fill.sha256,'Whole original Unlock buffer');assert.equal(raw.every(v=>v===0),chunk.fill.allZero);return raw;}
function normalized(raw){const floats=new Float32Array(raw.length/2);for(let i=0;i<floats.length;i++)floats[i]=raw.readInt16LE(i*2)/32768;return Buffer.from(floats.buffer);}
function collect(frames,partitions){const b=Buffer.alloc(frames*8);let at=0,index=0;while(at<frames){const n=Math.min(frames-at,partitions[index++%partitions.length]);mix(n).copy(b,at*8);at+=n;}return b;}
let comparedWords=0,differenceWords=0,firstFailure=null;const rows=[],excludedNativeRows=[];
for(const row of native.rows){
 if(row.track===0&&row.clockNs<22676){for(const chunk of row.chunks)rawChunk(chunk);excludedNativeRows.push({track:row.track,clockNs:row.clockNs,reason:'Signed SetFilePointer fails and retains prior asynchronous raw-file reader position; existing decoder fallback is not certified'});continue;}
 reset(row.track);c.clock_ns(BigInt(row.clockNs));assert.equal(c.save(),1);assert.equal(c.music(17),1,error());mix(1024);assert.equal(c.restore(),1,error());
 let words=0,different=0;const actualHash=createHash('sha256'),expectedHash=createHash('sha256');
 for(const chunk of row.chunks){const expected=normalized(rawChunk(chunk)),actual=collect(expected.length/8,[1024,127,997,23]);assert.equal(actual.length,expected.length);actualHash.update(actual);expectedHash.update(expected);
  const a=new Uint32Array(actual.buffer,actual.byteOffset,actual.length/4),b=new Uint32Array(expected.buffer,expected.byteOffset,expected.length/4);for(let i=0;i<a.length;i++)if(a[i]!==b[i]){different++;if(!firstFailure)firstFailure={track:row.track,clockNs:row.clockNs,word:words+i,actual:a[i],expected:b[i]};}words+=a.length;
 }
 comparedWords+=words;differenceWords+=different;rows.push({track:row.track,name:row.name,clockNs:row.clockNs,originalBufferChunks:row.chunks.length,loopReached:row.loopReached,words,differenceWords:different,actualSha256:actualHash.digest('hex'),originalNormalizedSha256:expectedHash.digest('hex')});
 if(row.clockNs===0||different)console.log(JSON.stringify({track:row.track,clockNs:row.clockNs,chunks:row.chunks.length,words,differenceWords:different}));
}
// Every stream must retain the ordinary seek contract after anomalous playback.
const controls=[];
for(let track=0;track<18;track++){
 const n=native.rows.find(r=>r.track===track),fmt=Buffer.from(n.formatHex,'hex'),offset=fmt.readUInt32LE(16),raw=Buffer.alloc(8192);readSync(bgm,raw,0,raw.length,offset);const expected=normalized(raw);
 reset(track);mix(997);assert.equal(c.save(),1);assert.equal(c.restore(),1);collect(190000,[997,1024]);assert.equal(c.music(cue(track)),1);const actual=collect(2048,[1,23,127,1024]);assert.equal(sha(actual),sha(expected),'Same-cue seek0 must cancel exceptional stream: '+track);
 reset(track);assert.equal(c.save(),1);c.mute(1);assert.equal(c.restore(),1);assert.ok(new Float32Array(mix(1024).buffer).every(v=>v===0),'Muted restore: '+track);c.mute(0);c.audio_pause(1);assert.ok(new Float32Array(mix(1024).buffer).every(v=>v===0),'Paused playback: '+track);c.audio_pause(0);assert.equal(c.save(),1);c.discard();assert.equal(c.restore(),0);
 // Partition changes must not change any PCM bytes, including exceptional stream boundaries.
 reset(track);assert.equal(c.save(),1);assert.equal(c.restore(),1);const regular=collect(190000,[1024]);reset(track);assert.equal(c.save(),1);assert.equal(c.restore(),1);const varied=collect(190000,[1,511,997,23]);assert.equal(sha(regular),sha(varied),'Partition dependence: '+track);
 controls.push({track,sameCueSeekZero:true,mutePauseDiscard:true,partitionIndependentFrames:190000,pcmSha256:sha(varied)});
}
// Retain the independently observed positive-time clock/loop cases. Advance
// by a nonaligned amount before saving, so node read-ahead cannot hide a seek.
const oldHome=resolve(root,'artifacts/th14/music-clock-native-v3-oct20'),oldNative=JSON.parse(bind(resolve(oldHome,'report.json'))),positiveRows=[];
assert.equal(oldNative.cases,216);
for(const [index,n] of oldNative.rows.entries()){
 if(n.retailSeconds===0)continue;
 const original=bind(resolve(oldHome,n.pcmFile));assert.equal(sha(original),n.pcmSha256);const expected=normalized(original);
 c.clock_ns(0n);assert.equal(c.audio_reset(),1);c.clock_ns(1250000000n);c.mute(0);assert.equal(c.music(cues.get(n.track)),1,error());mix(997);mix(127);
 c.audio_pause(1);c.clock_ns(1375000000n);c.audio_pause(0);if(n.pausedSeconds){c.audio_suspend(1);c.clock_ns(1875000000n);c.audio_suspend(0);}
 const saveClock=BigInt(n.counter-oldNative.origin)*100n;c.clock_ns(saveClock);assert.equal(c.save(),1);assert.equal(c.music(17),1);mix(997);c.clock_ns(saveClock+1234567890n);assert.equal(c.restore(),1,error());
 const actual=mix(1024).subarray(0,expected.length);assert.equal(sha(actual),sha(expected),'Positive clock '+index);
 positiveRows.push({index,name:n.track,words:expected.length/4,actualSha256:sha(actual),originalNormalizedSha256:sha(expected)});
}
assert.equal(positiveRows.length,180);
closeSync(bgm);
const musicFiles={};for(const row of native.rows.filter(r=>r.clockNs===0)){const name=row.name.replace(/\.wav$/,'.flac');musicFiles[name]=sha(bind(resolve(musicDir,name)));}
const result={passed:differenceWords===0,cases:rows.length,originalRestoreCases:108,excludedNativeRows,streamingCases:17,comparedWords,differenceWords,firstFailure,rows,controls,positiveClockCases:positiveRows.length,positiveClockWords:positiveRows.reduce((v,r)=>v+r.words,0),positiveRows,nativeReportSha256:sha(read(nativePath)),wasmSha256:sha(bytes),sourceArchiveSha256:sha(archive),musicFiles,bindings,audioDevicesOpened:0,audioPlayed:false,completeGame:false,nativeEquivalent:false,scope:'Whole retail481ee0 recreation,480cf0 initial fill,481620 streaming refills and481b40/481c40 seek/read with controlled COM, QPC and read-only file adapters.104 compared nanosecond clock cases over18 lossless FLAC tracks;17 zero-time streams continue across earlier-track ranges and current-track loop. Four first-track subframe cases remain excluded: real Windows signed seek failure retains prior reader state. No first-track zero-time equivalence is claimed. Production miniaudio mixer with deterministic silent SDL sink. Does not certify actual hardware notification timing, queued playback, Application Continue, full game or browser acceptance.'};
write(resolve(out,'comparison.json'),JSON.stringify(result,null,2)+'\n');assert(result.passed,JSON.stringify(firstFailure));console.log('PASS '+rows.length+' cases / '+comparedWords+' float words; no audio device');
