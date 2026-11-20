// Uses actual Replay/ReplayRecorder exports; synthetic recordings test format only.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,mkdtempSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {parseArgs} from 'node:util';
import {WASI} from 'node:wasi';
import {annotateTh14ReplayBeamRule} from '../runtimes/th12/portable/browser/th14-replay-beam-rules.mjs';
const {values}=parseArgs({options:{'parser-wasm':{type:'string'},'output-dir':{type:'string'}}});
assert(values['parser-wasm']&&values['output-dir'],'Specify --parser-wasm and --output-dir');
const O=resolve(values['output-dir']);mkdirSync(O,{recursive:true});
const bytes=readFileSync(values['parser-wasm']),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}});
const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const hash=b=>createHash('sha256').update(b).digest('hex'),cases=[];
function open(b){const p=c.viewer_alloc(b.length);assert(p);try{new Uint8Array(c.memory.buffer,p,b.length).set(b);return c.policy_open(p,b.length);}finally{c.viewer_free(p);}}
function record(touch){const n=c.policy_record(touch);assert(n);return Buffer.from(new Uint8Array(c.memory.buffer,c.policy_record_data(),n));}
let sample;
for(const touch of [0,1]){
 const tagged=record(touch);assert.equal(tagged.readUInt32LE(tagged.length-12),0x42343154);
 const original=Buffer.from(tagged.subarray(0,-20)),before=hash(original);sample=original;
 assert.equal(open(original),0);
 for(const rule of [0,1]){
  const out=annotateTh14ReplayBeamRule(original,rule);
  assert.equal(open(out),rule);assert.equal(out.length,original.length+20);
  assert.deepEqual(out.subarray(0,original.length),new Uint8Array(original));assert.equal(hash(original),before);
  assert.throws(()=>annotateTh14ReplayBeamRule(out,rule),/already declares/);
  cases.push(`actual parser accepts explicit rule ${rule}, touch ${touch}, original bytes preserved`);
 }
 const backing=Buffer.concat([Buffer.from([1,2]),original,Buffer.from([3])]);
 assert.equal(open(annotateTh14ReplayBeamRule(backing.subarray(2,-1),1)),1);cases.push(`nonzero input offset ${touch}`);
}
const unknown=Buffer.alloc(12);unknown.write('USER');unknown.writeUInt32LE(12,4);unknown.writeUInt32LE(123,8);
const extended=Buffer.concat([sample,unknown]);const result=annotateTh14ReplayBeamRule(extended,1);
assert.equal(open(result),1);assert.deepEqual(result.subarray(0,extended.length),new Uint8Array(extended));cases.push('unknown USER block preserved');
for(const bad of [Buffer.alloc(0),Buffer.alloc(36),Buffer.concat([sample,Buffer.from([1])]),Buffer.concat([sample,Buffer.alloc(12)]),Buffer.concat([sample,Buffer.from('USER')])]){assert.throws(()=>annotateTh14ReplayBeamRule(bad,1));cases.push('malformed container rejected');}
const badLength=Buffer.from(unknown);badLength.writeUInt32LE(0xffffffff,4);assert.throws(()=>annotateTh14ReplayBeamRule(Buffer.concat([sample,badLength]),1));cases.push('oversized USER block rejected');
for(const rule of [undefined,-1,2,'bounded']){assert.throws(()=>annotateTh14ReplayBeamRule(sample,rule));cases.push('missing or invalid explicit rule rejected');}
const dir=mkdtempSync(resolve(O,'cli-')),input=resolve(dir,'input.rpy'),output=resolve(dir,'bounded.rpy');writeFileSync(input,sample);
const cli=resolve(import.meta.dirname,'th14-annotate-replay-beam-rule.mjs');
function run(args){return spawnSync(process.execPath,[cli,...args],{encoding:'utf8',windowsHide:true});}
const args=['--input',input,'--output',output,'--rule','bounded','--expect-sha256',hash(sample)];
assert.equal(run(args).status,0);assert.equal(open(readFileSync(output)),1);cases.push('CLI creates explicit bounded copy');
const savedHash=hash(readFileSync(output));assert.notEqual(run(args).status,0);assert.equal(hash(readFileSync(output)),savedHash);cases.push('CLI refuses overwrite');
assert.notEqual(run(['--input',input,'--output',resolve(dir,'bad.rpy'),'--rule','bounded','--expect-sha256','0'.repeat(64)]).status,0);cases.push('CLI rejects mismatched input hash');
assert.notEqual(run(['--input',input,'--output',input,'--rule','bounded','--expect-sha256',hash(sample)]).status,0);assert.equal(hash(readFileSync(input)),hash(sample));cases.push('CLI refuses original path');
const q={passed:true,cases,parserSha256:hash(bytes),sourceSha256:hash(readFileSync(resolve(import.meta.dirname,'../runtimes/th12/portable/browser/th14-replay-beam-rules.mjs'))),syntheticFormatCasesOnly:true,actualHistoricalPlaybackAccepted:false,noGameAssets:true,silent:true,completeGame:false};
writeFileSync(resolve(O,'qualified.json'),JSON.stringify(q,null,2)+'\n');console.log(JSON.stringify({passed:true,cases:cases.length,actualHistoricalPlaybackAccepted:false}));
