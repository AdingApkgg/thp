import assert from 'node:assert/strict';import{readFileSync,writeFileSync}from'node:fs';import{resolve}from'node:path';import{createHash}from'node:crypto';import{WASI}from'node:wasi';
const R=resolve(import.meta.dirname,'..'),H=resolve(R,'artifacts/th14/camera-right-pair-nov12'),sha=b=>createHash('sha256').update(b).digest('hex'),read=p=>readFileSync(p),load=p=>JSON.parse(read(p));
const reports=[];
for(const mode of ['baseline','candidate']){
 const O=resolve(H,mode+'-component'),b=load(resolve(O,'build.json')),bytes=read(resolve(O,'probe.wasm'));assert.equal(sha(bytes),b.wasmSha256);
 for(const [p,d]of Object.entries(b.sourceBindings))assert.equal(sha(read(resolve(b.sourceRoot,p))),d,p);
 for(const [p,d]of Object.entries(b.objectBindings))assert.equal(sha(read(resolve(R,p))),d,p);
 assert.equal(sha(read(resolve(R,'tools/th14-camera-right-pair-component-nov12.cpp'))),b.fixtureSha256);
 const module=new WebAssembly.Module(bytes),memory=new WebAssembly.Memory({initial:256,maximum:16384,shared:true}),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{},returnOnExit:true});
 const imports={wasi_snapshot_preview1:wasi.wasiImport};for(const e of WebAssembly.Module.imports(module)){if(e.module==='wasi_snapshot_preview1')continue;imports[e.module]??={};imports[e.module][e.name]=e.kind==='memory'?memory:()=>{throw Error('Unexpected '+e.module+'.'+e.name);};}
 const instance=new WebAssembly.Instance(module,imports);wasi.initialize(instance);const c=instance.exports,m=c.memory??memory;
 const layout=Array.from(new Uint32Array(m.buffer,c.layout_data(),8));assert.equal(layout[0],300);assert.equal(layout[1],4);assert.equal(layout[7],48);
 if(mode==='candidate'){assert.equal(layout[3],8);assert.equal(layout[4]%8,0);assert.equal(layout[5],0);assert.equal(layout[6],0);}
 const run=(input,perspective,offset)=>{new Uint8Array(m.buffer,c.input_data(),300).set(input);c.compute(Number(perspective),offset);return Buffer.from(new Uint8Array(m.buffer,c.output_data(),300));};
 let cases=0,controls=0,perspectivePhases=0;const rows=[];
 for(const db of ['menu-camera-derived-nov06/native','camera-cached-derived-nov06/native-cpu']){
  const P=resolve(R,'artifacts/th14',db),native=load(resolve(P,'report.json')),inputs=read(resolve(P,'inputs.u32')),expected=read(resolve(P,'expected.u32'));
  assert.equal(sha(inputs),native.inputsSha256);assert.equal(sha(expected),native.expectedSha256);
  for(const [index,info]of native.rows.entries())for(const offset of [0,4]){
   const input=inputs.subarray(index*300,(index+1)*300),ref=expected.subarray(index*300,(index+1)*300),actual=run(input,info.mode==='perspective',offset);assert(actual.equals(ref),JSON.stringify({mode,db,index,offset}));cases++;
   if(info.mode==='perspective'){
    const phases=Array.from(new Uint32Array(m.buffer,c.phase_data(),c.phase_size()*4));assert.deepEqual(phases.filter((_,i)=>i%4===0),[0,1,2,3,4,6,7,5]);
    assert.deepEqual(phases.slice(3*4+3,3*4+4),phases.slice(2*4+3,2*4+4));
    const final=[actual.readUInt32LE(12*4),actual.readUInt32LE(13*4),actual.readUInt32LE(14*4)];assert.equal(phases[5*4+1],final[0]);assert.equal(phases[6*4+2],final[1]);assert.deepEqual(phases.slice(7*4+1,8*4),final);perspectivePhases++;
   }
   const altered=Buffer.from(input);altered.writeFloatLE(altered.readFloatLE(21*4)*.875,21*4);const changed=run(altered,info.mode==='perspective',offset);assert(!actual.subarray(24*4,56*4).equals(changed.subarray(24*4,56*4)));controls++;
   rows.push({db,index,offset,mode:info.mode,all75WordsEqual:true,sha256:sha(actual)});
  }
 }
 assert.equal(cases,80);assert.equal(controls,80);const report={mode,cases,fovPositiveControls:controls,perspectivePhaseChecks:perspectivePhases,all75WordsEqual:true,alignedAndUnalignedPrivateCameraChecked:true,sharedOwnerLayout:layout,normalAccess:true,wasmSha256:sha(bytes),rows,newGameRuns:0,newGpuRuns:0,completeGame:false};writeFileSync(resolve(O,'checked.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});reports.push(report);console.log(JSON.stringify({mode,cases,perspectivePhases,layout}));
}
assert.deepEqual(reports[0].rows.map(r=>r.sha256),reports[1].rows.map(r=>r.sha256));
