import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync}from'node:fs';
import {resolve}from'node:path';
import {createHash}from'node:crypto';
import {WASI}from'node:wasi';
const R=resolve(import.meta.dirname,'..'),H=resolve(R,'artifacts/th14/quad-display-space-nov12',process.argv[3]==='rotations'?'rotations':'.'),mode=process.argv[2];assert(['baseline','candidate'].includes(mode));
const read=p=>readFileSync(p),sha=b=>createHash('sha256').update(b).digest('hex'),load=p=>JSON.parse(read(p));
const native=load(resolve(H,'native.json')),inputs=read(resolve(H,'inputs.bin')),submit=load(resolve(H,'native-submit-query/native.json'));assert.equal(sha(inputs),native.inputSha256);const destination=resolve(H,(process.argv[4]??mode)+'-submit-query');mkdirSync(destination);
const moduleDirectory=process.argv[4]??mode;const build=load(resolve(H,moduleDirectory,'build.json')),wasm=read(resolve(H,moduleDirectory,'probe.wasm'));assert.equal(sha(wasm),build.wasmSha256);
const module=new WebAssembly.Module(wasm),memory=new WebAssembly.Memory({initial:1024,maximum:16384,shared:true}),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{},returnOnExit:true}),imports={wasi_snapshot_preview1:wasi.wasiImport};
for(const e of WebAssembly.Module.imports(module)){if(e.module==='wasi_snapshot_preview1')continue;imports[e.module]??={};if(e.kind==='memory')imports[e.module][e.name]=memory;else{assert.equal(e.kind,'function');imports[e.module][e.name]=()=>{throw Error('Unexpected service '+e.module+'.'+e.name);};}}
const instance=new WebAssembly.Instance(module,imports);wasi.initialize(instance);const c=instance.exports,mem=c.memory??memory,reports=[];
for(const ascii of [0,1]){
 const route=ascii?'ascii':'draw',bound=submit.routes.find(x=>x.route===route),expected=read(resolve(H,'native-submit-query',bound.path));assert.equal(sha(expected),bound.sha256);
 const differences=[],byWidth={},hash=createHash('sha256');let compared=0;
 for(let i=0;i<native.cases;i++){
  const row=native.rows[i];new Uint8Array(mem.buffer,c.input_ptr(),3000).set(inputs.subarray(row.input*3000,(row.input+1)*3000));assert.equal(c.run_quad(row.mode,row.anchor,ascii),12);
  const actual=Buffer.from(new Uint8Array(mem.buffer,c.output_ptr(),48));hash.update(actual);const fields=[];
  for(let j=0;j<12;j++){const a=actual.readUInt32LE(j*4),b=expected.readUInt32LE((i*12+j)*4);++compared;if(a!==b)fields.push({index:j,actual:a,expected:b});}
  byWidth[row.width]??={cases:0,failed:0};byWidth[row.width].cases++;if(fields.length){byWidth[row.width].failed++;differences.push({case:i,input:row,fields});}
 }
 reports.push({route:ascii?'ascii':'draw',cases:native.cases,wordsCompared:compared,failedCases:differences.length,differentWords:differences.reduce((n,x)=>n+x.fields.length,0),byWidth,actualOutputSha256:hash.digest('hex'),nativeOutputSha256:bound.sha256});
 writeFileSync(resolve(destination,ascii?'ascii-private-differences.json':'draw-private-differences.json'),JSON.stringify(differences,null,2)+'\n',{flag:'wx'});
}
const report={mode,originalSubmitSlice:submit.actualOriginalSubmitSlice,checkerSha256:sha(read(import.meta.filename)),routes:reports,wasmSha256:sha(wasm),normalProviderAccess:true,allRotationsZero:native.allRotationsZero,newGameRuns:0,newGpuRuns:0,audibleOutput:false,completeGame:false};writeFileSync(resolve(destination,'checked.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify(report));
for(const r of reports)if(mode==='baseline')assert(r.failedCases>0);else assert.equal(r.failedCases,0);
