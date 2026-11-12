import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),out=resolve(root,'artifacts/th14/replay-entry-position-nov13');
const load=n=>JSON.parse(readFileSync(resolve(out,n))),build=load('build.json'),native=load('native.json');
const sha=b=>createHash('sha256').update(b).digest('hex');
for(const [p,h]of Object.entries({...build.sourceBindings,...build.objects}))assert.equal(sha(readFileSync(resolve(root,p))),h,p);
const results={},headers={};
for(const mode of ['baseline','candidate']){
 const bytes=readFileSync(resolve(out,mode+'.wasm'));assert.equal(sha(bytes),build.wasm[mode]);
 const module=new WebAssembly.Module(bytes),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}});
 const imports={wasi_snapshot_preview1:wasi.wasiImport,env:{memory:new WebAssembly.Memory({initial:1024,maximum:16384,shared:true})}};
 for(const x of WebAssembly.Module.imports(module)){
  imports[x.module]??={};if(x.kind==='function'&&!imports[x.module][x.name])imports[x.module][x.name]=()=>{throw Error('Unexpected platform call '+x.module+'.'+x.name);};
 }
 const instance=new WebAssembly.Instance(module,imports);wasi.initialize(instance);
 const rows=[];headers[mode]=[];
 for(let selection=0;selection<6;selection++)for(let difficulty=0;difficulty<5;difficulty++)for(let practice=0;practice<2;practice++)for(let initial=0;initial<2;initial++)for(const [x,y]of build.coords){
  const expected=native.rows.find(r=>r.initial===initial&&r.input[0]===x&&r.input[1]===y).output;
  const ptr=instance.exports.run(selection,difficulty,practice,initial,x,y);
  const h=Buffer.from(new Uint8Array(imports.env.memory.buffer,ptr,instance.exports.header_size()));
  const actual=[h.readInt32LE(12),h.readInt32LE(16)];assert.equal(h.readUInt32LE(0xd8),initial);
  rows.push({selection,difficulty,practice,initial,input:[x,y],actual,expected});headers[mode].push(h);
 }
 results[mode]={cases:rows.length,different:rows.filter(r=>r.actual.some((v,i)=>v!==r.expected[i])).length,rows};
 writeFileSync(resolve(out,mode+'-headers.bin'),Buffer.concat(headers[mode]),{flag:'wx'});
}
assert.equal(results.baseline.different,240);assert.equal(results.candidate.different,0);
for(let n=0;n<headers.baseline.length;n++){
 const a=Buffer.from(headers.baseline[n]),b=Buffer.from(headers.candidate[n]);
 // Full retained headers remain evidence; this comparison isolates this edit's footprint.
 a.fill(0,12,20);b.fill(0,12,20);assert(a.equals(b),'Unrelated header bytes changed at '+n);
}
const report={results,headerBytes:headers.baseline[0].length,allOtherHeaderBytesUnchanged:true,
 actualSessionAndRecorderUsed:true,controlledMetadataOnly:true,assetsLoaded:false,
 normalPlayerInitializationOrCompleteReplayAccepted:false,productionChanged:false,completeGame:false,
 bindings:{build:sha(readFileSync(resolve(out,'build.json'))),fixture:build.fixtureSha256,runner:sha(readFileSync(import.meta.filename)),
 baselineHeaders:sha(readFileSync(resolve(out,'baseline-headers.bin'))),candidateHeaders:sha(readFileSync(resolve(out,'candidate-headers.bin')))}};
writeFileSync(resolve(out,'result.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({cases:results.candidate.cases,baselineDifferent:results.baseline.different,candidateDifferent:results.candidate.different,allOtherHeaderBytesUnchanged:true}));
