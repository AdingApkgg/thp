import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),out=resolve(root,'artifacts/th14/replay-entry-flag-nov13');
const load=n=>JSON.parse(readFileSync(resolve(out,n)));
const build=load('build.json'),native=load('native.json');
const sha=b=>createHash('sha256').update(b).digest('hex');
for(const [p,h]of Object.entries(build.objects))assert.equal(sha(readFileSync(resolve(root,p))),h,p);
const results={};
for(const mode of ['baseline','candidate']){
 const bytes=readFileSync(resolve(out,mode+'.wasm'));assert.equal(sha(bytes),build.wasm[mode]);
 const module=new WebAssembly.Module(bytes),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}});
 const imports={wasi_snapshot_preview1:wasi.wasiImport,env:{memory:new WebAssembly.Memory({initial:1024,maximum:16384,shared:true})}};
 for(const x of WebAssembly.Module.imports(module)){
  imports[x.module]??={};if(x.kind==='function'&&!imports[x.module][x.name])imports[x.module][x.name]=()=>{throw Error('Unexpected platform call '+x.module+'.'+x.name);};
 }
 const instance=new WebAssembly.Instance(module,imports);wasi.initialize(instance);
 const rows=[];
 for(let selection=0;selection<6;selection++)for(let difficulty=0;difficulty<5;difficulty++)for(let practice=0;practice<2;practice++)for(let initial=0;initial<2;initial++){
  const expected=native.rows.find(x=>Number(x.initial)===initial&&x.old===0).headerD8;
  const actual=instance.exports.run(selection,difficulty,practice,initial);
  rows.push({selection,difficulty,practice,initial,actual,expected});
 }
 results[mode]={cases:rows.length,different:rows.filter(x=>x.actual!==x.expected).length,rows};
}
assert.equal(results.baseline.different,60);
assert.equal(results.candidate.different,0);
const report={results,actualSessionRecordingFunction:true,actualGameBattleAndPlayerConstructors:true,
 controlledMetadataOnly:true,assetsLoaded:false,fullOrdinaryFlowAccepted:false,completeReplayOrSaveAccepted:false,
 originalBitProducersAndHeaderMergeCases:native.rows.length,productionChanged:false,completeGame:false,
 buildSha256:sha(readFileSync(resolve(out,'build.json'))),toolSha256:sha(readFileSync(import.meta.filename))};
writeFileSync(resolve(out,'result.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({baselineDifferences:results.baseline.different,candidateDifferences:results.candidate.different,cases:results.candidate.cases,completeGame:false}));
