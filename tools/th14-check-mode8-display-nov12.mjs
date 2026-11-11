import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),home=resolve(root,'artifacts/th14/mode8-display-space-nov12');
const mode=process.argv[2];assert(['baseline','candidate'].includes(mode));
const read=p=>readFileSync(p),sha=b=>createHash('sha256').update(b).digest('hex'),load=p=>JSON.parse(read(p));
const oracle=load(resolve(home,'native.json')),input=read(resolve(home,'inputs.bin')),expected=read(resolve(home,'outputs.u32'));
assert.equal(sha(input),oracle.inputSha256);assert.equal(sha(expected),oracle.outputSha256);
assert.equal(input.length,oracle.cases*oracle.inputStrideBytes);assert.equal(expected.length,oracle.cases*33*4);
const dir=resolve(home,process.argv[3]??mode),build=load(resolve(dir,'build.json')),wasm=read(resolve(dir,'probe.wasm'));assert.equal(sha(wasm),build.wasmSha256);
const module=new WebAssembly.Module(wasm),memory=new WebAssembly.Memory({initial:1024,maximum:16384,shared:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{},returnOnExit:true}),imports={wasi_snapshot_preview1:wasi.wasiImport};
for(const entry of WebAssembly.Module.imports(module)){
 if(entry.module==='wasi_snapshot_preview1')continue;
 imports[entry.module]??={};
 if(entry.kind==='memory'){assert.equal(entry.name,'memory');imports[entry.module][entry.name]=memory;}
 else {assert.equal(entry.kind,'function');imports[entry.module][entry.name]=()=>{throw Error('Unexpected service '+entry.module+'.'+entry.name);};}
}
const instance=new WebAssembly.Instance(module,imports);wasi.initialize(instance);const c=instance.exports;
const variant=process.argv[4]??'matrix';assert(['matrix','renderer'].includes(variant));
const actualMemory=c.memory??memory,outputs=createHash('sha256'),differences=[],byWidth={};let words=0,failed=0;
for(let i=0;i<oracle.cases;i++){
 new Uint8Array(actualMemory.buffer,c.input_ptr(),oracle.inputStrideBytes).set(input.subarray(i*oracle.inputStrideBytes,(i+1)*oracle.inputStrideBytes));
 assert.equal(variant==='matrix'?c.run():c.run_draw(),33);
 const out=Buffer.from(new Uint8Array(actualMemory.buffer,c.output_ptr(),33*4));outputs.update(out);
 const fields=[];
 for(let j=0;j<33;j++){const a=out.readUInt32LE(j*4),e=expected.readUInt32LE((i*33+j)*4);++words;if(a!==e)fields.push({index:j,actual:a,expected:e});}
 const width=oracle.rows[i].width;byWidth[width]??={cases:0,failed:0,wordsDifferent:0};byWidth[width].cases++;
 if(fields.length){failed++;byWidth[width].failed++;byWidth[width].wordsDifferent+=fields.length;differences.push({case:i,input:oracle.rows[i],fields});}
}
const report={mode,variant,cases:oracle.cases,wordsCompared:words,failedCases:failed,differentWords:differences.reduce((n,r)=>n+r.fields.length,0),byWidth,
 actualOutputSha256:outputs.digest('hex'),nativeOutputSha256:oracle.outputSha256,currentWasmSha256:sha(wasm),checkerSha256:sha(read(import.meta.filename)),
 originalMatrixCodeComparedExactly:true,normalProviderAccess:true,originalOsGameRuns:0,gpuRuns:0,audibleOutput:false,completeGame:false};
writeFileSync(resolve(dir,'checked.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
writeFileSync(resolve(dir,'private-differences.json'),JSON.stringify(differences,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(report));
if(mode==='baseline')assert(failed>0,'Need an actual failing parent');else assert.equal(failed,0);
