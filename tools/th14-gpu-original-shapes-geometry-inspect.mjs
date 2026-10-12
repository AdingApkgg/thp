import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {WASI} from 'node:wasi';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),read=p=>readFileSync(resolve(root,p)),sha=b=>createHash('sha256').update(b).digest('hex');
const dir='artifacts/th14/gpu-original-quads/geometry/',oracle=JSON.parse(read(dir+'native.json')),bytes=read(dir+'th14.wasm');
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const rows=[];
for(const [index,row] of oracle.shapes.entries()){
 c.shape_case(row.mode,row.anchor,row.parent,row.resolution);const differences=[];
 for(const [j,d] of row.draws.entries())for(const [i,v] of d.vertices.entries())for(const f of [0,1,2,3]){
  const actual=c.shape_component(j,i,f);if(actual!==v[f])differences.push({draw:j,vertex:i,field:f,native:v[f],portable:actual,delta:actual-v[f]});
 }
 rows.push({index,mode:row.mode,anchor:row.anchor,parent:row.parent,resolution:row.resolution,differences});
}
const report={scope:'Exact float32 vertex inspection, separate from tolerance-based geometry acceptance and actual GPU pixel acceptance',nativeOracleSha256:sha(read(dir+'native.json')),wasmSha256:sha(bytes),cases:rows.length,exactVertexCases:rows.filter(r=>!r.differences.length).length,differentComponents:rows.reduce((a,r)=>a+r.differences.length,0),rows};
writeFileSync(resolve(root,'artifacts/th14/gpu-original-shapes/geometry-inspection.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({...report,rows:rows.filter(r=>r.differences.length).slice(0,10)}));
