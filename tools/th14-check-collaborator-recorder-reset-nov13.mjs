import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),home=resolve(root,'artifacts/th14/collaborator-practice-review-nov13/recorder-reset');
const sha=b=>createHash('sha256').update(b).digest('hex'),build=JSON.parse(readFileSync(resolve(home,'build.json'))),results={};
for(const variant of ['before','fixed']){
 const bytes=readFileSync(resolve(home,variant,'probe.wasm'));assert.equal(sha(bytes),build.outputs[variant].wasmSha256);
 const module=new WebAssembly.Module(bytes),memory=new WebAssembly.Memory({initial:1024,maximum:16384,shared:true});
 const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),imports={env:{memory},wasi_snapshot_preview1:wasi.wasiImport};
 for(const item of WebAssembly.Module.imports(module)){
  imports[item.module]??={};if(item.kind==='function'&&!imports[item.module][item.name])imports[item.module][item.name]=()=>{throw Error('Unexpected boundary '+item.module+'.'+item.name);};
 }
 const instance=new WebAssembly.Instance(module,imports);wasi.initialize(instance);const rows=[];
 for(let selection=0;selection<6;selection++)for(let difficulty=0;difficulty<5;difficulty++)for(let practice=0;practice<2;practice++){
  const actual=instance.exports.check(selection,difficulty,practice)>>>0;
  rows.push({selection,difficulty,practice,mode:actual&255,stalePracticeStage:actual>>>8&255,events:actual>>>16,passed:actual===practice});
 }
 results[variant]={cases:rows.length,passed:rows.filter(r=>r.passed).length,modeFailures:rows.filter(r=>r.mode!==r.practice).length,staleSettingsFailures:rows.filter(r=>r.stalePracticeStage!==0).length,rows};
}
assert.equal(results.before.passed,0);assert.equal(results.before.modeFailures,30);assert.equal(results.before.staleSettingsFailures,60);
assert.equal(results.fixed.passed,60);assert.equal(results.fixed.modeFailures,0);assert.equal(results.fixed.staleSettingsFailures,0);
const report={passed:true,actualPatchedCppRecorder:true,results,silent:true,assetsLoaded:false,gameplayOrBrowserAccepted:false,completeGame:false,runnerSha256:sha(readFileSync(import.meta.filename))};
writeFileSync(resolve(home,'qualified.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:true,before:results.before.passed,fixed:results.fixed.passed,modeFailuresBefore:30,staleSettingsFailuresBefore:60}));
