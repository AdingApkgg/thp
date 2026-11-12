// v2: open_track closes the prior decoder; retain layouts until final close.
// Memory-only decoding: no SDL/audio output device is opened.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,existsSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const home=dirname(fileURLToPath(import.meta.url)),music=process.argv[2];assert(music);
const read=p=>readFileSync(resolve(home,p)),load=p=>JSON.parse(read(p)),sha=b=>createHash('sha256').update(b).digest('hex');
const plan=load('validation-input.json'),bytes=read('probe.wasm'),formats=read('thbgm.fmt');
assert.equal(sha(bytes),plan.decoderWasmSha256);assert.equal(sha(formats),plan.formatSha256);assert.equal(plan.tracks.length,18);
assert.equal(plan.sampleTolerance,0.0001);assert(!existsSync(resolve(home,'result.json')));
const module=await WebAssembly.compile(bytes),env={};let unexpectedPlatformCalls=0;
for(const i of WebAssembly.Module.imports(module))if(i.module==='env'&&i.kind==='function')env[i.name]=()=>{++unexpectedPlatformCalls;throw Error('Unexpected platform '+i.name);};
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{'/music':music},returnOnExit:true});
const instance=await WebAssembly.instantiate(module,{env,wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);
const c=instance.exports,memory=c.memory,p=c.allocate(formats.length);new Uint8Array(memory.buffer,p,formats.length).set(formats);
assert.equal(c.set_formats(p,formats.length),formats.length);c.release(p);
const rows=[];let exception=null,activeChild=null,totalFrames=0;
try{
 for(const track of plan.tracks){
  const file=resolve(music,track.file),encoded=readFileSync(file);assert.equal(sha(encoded),track.sha256);assert.equal(encoded.subarray(0,4).toString(),'OggS');
  const wav=track.file.replace(/\.ogg$/,'.wav');let index=-1;
  for(let i=0;i*52+52<=formats.length;++i)if(formats.subarray(i*52,i*52+16).toString().split('\0')[0]===wav){index=i;break;}
  assert(index>=0,wav);const meta=Array.from(new Uint32Array(memory.buffer,c.open_track(index),12));
  assert.deepEqual(meta,[0,track.frames,0,track.frames,track.loopFrame,44100,2,1,1,0,index,4],track.file);
  const windows=[0,track.loopFrame,track.frames-128].map(start=>({start,bytes:Buffer.alloc(128*8),filled:0}));
  let frame=0,maxError=0,aboveTolerance=0,numericDifferences=0,remainder=Buffer.alloc(0),stderr='';
  const actualHash=createHash('sha256'),referenceHash=createHash('sha256');
  const child=spawn('ffmpeg',['-v','error','-i',file,'-map','0:a:0','-acodec','pcm_f32le','-f','f32le','pipe:1'],{stdio:['ignore','pipe','pipe'],windowsHide:true});activeChild=child;
  const exited=new Promise((res,rej)=>{child.on('error',rej);child.on('close',(code,signal)=>res({code,signal}));});
  child.stderr.on('data',b=>{stderr=(stderr+b.toString()).slice(-8000);});
  const watchdog=setTimeout(()=>child.kill('SIGTERM'),120000);
  try{
   for await(const part of child.stdout){
    const data=remainder.length?Buffer.concat([remainder,part]):part;let offset=0;
    while(offset+8<=data.length){
     const count=Math.min(4096,Math.floor((data.length-offset)/8));
     assert.equal(c.read_raw(count),count,'Production EOF differs from independent FFmpeg '+track.file+' @'+frame+' error='+c.last_error());
     const actual=Buffer.from(memory.buffer,c.sample_data(),count*8),reference=data.subarray(offset,offset+count*8);
     actualHash.update(actual);referenceHash.update(reference);
     for(let i=0;i<count*2;++i){const a=actual.readFloatLE(i*4),b=reference.readFloatLE(i*4);assert(Number.isFinite(a)&&Number.isFinite(b));const d=Math.abs(a-b);if(d>maxError)maxError=d;if(d>plan.sampleTolerance)++aboveTolerance;if(a!==b)++numericDifferences;}
     for(const w of windows){const first=Math.max(frame,w.start),last=Math.min(frame+count,w.start+128);if(last>first){actual.copy(w.bytes,(first-w.start)*8,(first-frame)*8,(last-frame)*8);w.filled+=last-first;}}
     frame+=count;offset+=count*8;
    }
    remainder=Buffer.from(data.subarray(offset));
   }
   const exit=await exited;assert.deepEqual(exit,{code:0,signal:null},stderr);
  }finally{clearTimeout(watchdog);if(child.exitCode===null&&child.signalCode===null){child.kill('SIGTERM');await exited;}activeChild=null;}
  assert.equal(remainder.length,0);assert.equal(frame,track.frames,'Decoded Vorbis frame count '+track.file);
  assert.equal(c.read_raw(1),0,'Extra production decoder PCM after expected end');assert(windows.every(w=>w.filled===128));
  let seekDifferentBytes=0;
  for(const w of windows){assert.equal(c.loop_stream(0),0);assert.equal(c.seek_stream(w.start),0);assert.equal(c.read_stream(128),128);
   const actual=Buffer.from(memory.buffer,c.sample_data(),128*8);for(let i=0;i<actual.length;++i)if(actual[i]!==w.bytes[i])++seekDifferentBytes;assert.equal(c.cursor(),w.start+128);}
  assert.equal(c.loop_stream(1),0);assert.equal(c.seek_stream(track.frames-64),0);assert.equal(c.read_stream(192),192);
  const loop=Buffer.from(new Uint8Array(memory.buffer,c.sample_data(),192*8));
  const expectedLoop=Buffer.concat([windows[2].bytes.subarray(64*8),windows[1].bytes]);let loopDifferentBytes=0;
  for(let i=0;i<loop.length;++i)if(loop[i]!==expectedLoop[i])++loopDifferentBytes;
  assert.equal(c.cursor(),track.loopFrame+128);
  assert.equal(c.seek_stream(track.loopFrame+1),0);assert.equal(c.read_stream(127),127);
  const shifted=Buffer.from(memory.buffer,c.sample_data(),127*8);let shiftedMaxError=0;
  for(let i=0;i<127*2;++i)shiftedMaxError=Math.max(shiftedMaxError,Math.abs(shifted.readFloatLE(i*4)-windows[1].bytes.readFloatLE(i*4)));
  totalFrames+=frame;
  const row={file:track.file,frames:frame,loopFrame:track.loopFrame,allSamplesComparedToIndependentFfmpeg:true,
   sampleTolerance:plan.sampleTolerance,maxAbsoluteError:maxError,aboveToleranceSamples:aboveTolerance,numericDifferentSamples:numericDifferences,
   actualDecodedFloatSha256:actualHash.digest('hex'),independentFfmpegFloatSha256:referenceHash.digest('hex'),
   seekWindows:3,seekDifferentBytes,loopBoundaryFrames:192,loopDifferentBytes,
   shiftedSeekControlMaxError:shiftedMaxError,shiftedSeekControlDetected:shiftedMaxError>plan.sampleTolerance,
   passed:aboveTolerance===0&&seekDifferentBytes===0&&loopDifferentBytes===0};
  rows.push(row);writeFileSync(resolve(home,'progress.json'),JSON.stringify({tracks:rows.length,totalFrames,latest:row},null,2)+'\n');console.log(JSON.stringify(row));
 }
}catch(e){exception=String(e?.stack??e);}finally{c.close();if(activeChild){activeChild.kill('SIGTERM');await new Promise(res=>activeChild.on('close',res));}}
const result={passed:exception===null&&rows.length===18&&rows.every(r=>r.passed)&&unexpectedPlatformCalls===0,
 sourceCommit:plan.sourceCommit,tracks:rows.length,totalDecodedStereoFrames:totalFrames,exception,rows,
 fullTrackIndependentDecoderComparison:true,codecToleranceFixedBeforeExecution:plan.sampleTolerance,
 seeksAndLoopsComparedBitExactlyToSameDecoderSequentialOutput:true,outputDeviceOpened:false,
 unexpectedPlatformCalls,actualBrowserPlaybackOrFinalMixerAccepted:false,originalPcmBitEqualityAccepted:false,
 productionChanged:false,completeGame:false,bindings:{wasm:sha(bytes),formats:sha(formats),plan:sha(read('validation-input.json')),runner:sha(readFileSync(fileURLToPath(import.meta.url)))}};
writeFileSync(resolve(home,'result.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({...result,rows:undefined}));if(!result.passed)process.exitCode=1;
