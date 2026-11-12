import assert from'node:assert/strict';import{readFileSync,writeFileSync}from'node:fs';import{resolve}from'node:path';import{createHash}from'node:crypto';import{WASI}from'node:wasi';
const R=resolve(import.meta.dirname,'..'),H=resolve(R,'artifacts/th14/mode8-rotation-nov12'),read=p=>readFileSync(p),sha=b=>createHash('sha256').update(b).digest('hex'),load=p=>JSON.parse(read(p));
const n=load(resolve(H,'native.json')),service=load(resolve(H,'native-services.json')),b=load(resolve(H,'component/build.json')),bytes=read(resolve(H,'component/probe.wasm')),input=read(resolve(H,'inputs.bin')),expected=read(resolve(H,'outputs.u32'));
assert.equal(n.cases,3456);assert.equal(sha(input),n.inputSha256);assert.equal(sha(expected),n.outputSha256);assert.equal(sha(bytes),b.wasmSha256);assert(service.workerExited&&service.workerExitCode===0);
for(const [p,d]of Object.entries({...b.sourceBindings,...b.objectBindings,...b.fixtureParentBindings}))assert.equal(sha(read(resolve(R,p))),d,p);
assert.equal(sha(read(resolve(H,'component/renderer-derived.cpp'))),b.fixtureSha256);assert.equal(sha(read(resolve(H,'component/matrix-derived.cpp'))),b.matrixFixtureSha256);
const module=new WebAssembly.Module(bytes),memory=new WebAssembly.Memory({initial:1024,maximum:16384,shared:true}),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{},returnOnExit:true}),imports={wasi_snapshot_preview1:wasi.wasiImport};
for(const e of WebAssembly.Module.imports(module)){if(e.module==='wasi_snapshot_preview1')continue;imports[e.module]??={};imports[e.module][e.name]=e.kind==='memory'?memory:()=>{throw Error('Unexpected service '+e.module+'.'+e.name);};}
const instance=new WebAssembly.Instance(module,imports);wasi.initialize(instance);const c=instance.exports,m=c.memory??memory,reports=[];
for(const route of ['matrix','renderer']){
 let words=0,different=0;const first=[],rows=[];
 for(let i=0;i<n.cases;i++){
  new Uint8Array(m.buffer,c.input_ptr(),n.inputStrideBytes).set(input.subarray(i*n.inputStrideBytes,(i+1)*n.inputStrideBytes));assert.equal(route==='matrix'?c.run():c.run_draw(),33);
  const actual=Buffer.from(m.buffer,c.output_ptr(),132);let errors=0;
  for(let w=0;w<33;w++){words++;const a=actual.readUInt32LE(w*4),e=expected.readUInt32LE(i*132+w*4);if(a!==e){different++;errors++;if(first.length<24)first.push({case:i,...n.rows[i],word:w,native:e,cpp:a});}}
  rows.push({case:i,order:n.rows[i].order,width:n.rows[i].width,differentWords:errors});
 }
 const report={route,cases:n.cases,comparedWords:words,differentWords:different,failedCases:rows.filter(r=>r.differentWords).length,rows,firstDifferences:first,wasmSha256:sha(bytes),actualOriginalMode8BranchesWithDeclaredRealD3dxServices:true,actualCurrentCppRoute:true,originalGameFpuEnvironmentNotInherited:true,syntheticSpriteMatricesAndVmInputs:true,gpuPixelsCompared:false,gameSourceChanged:false,newGameRuns:0,newGpuRuns:0,completeGame:false};writeFileSync(resolve(H,`checked-${route}.json`),JSON.stringify(report,null,2)+'\n',{flag:'wx'});reports.push(report);console.log(JSON.stringify({route,cases:n.cases,comparedWords:words,differentWords:different,failedCases:report.failedCases,first:first.slice(0,4)}));
}
assert(reports.every(r=>r.differentWords===0));
