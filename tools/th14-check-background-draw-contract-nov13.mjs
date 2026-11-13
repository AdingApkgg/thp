import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),out=resolve(root,'artifacts/th14/background-draw-contract-v2-nov13');
const sha=b=>createHash('sha256').update(b).digest('hex'),load=p=>JSON.parse(readFileSync(p));
const build=load(resolve(out,'build.json')),reference=load(resolve(out,'result.json'));
for(const [p,h]of Object.entries({...build.sourceBindings,...build.objectBindings,...reference.bindings}))assert.equal(sha(readFileSync(resolve(root,p))),h,p);
const bytes=readFileSync(resolve(out,'current.wasm'));assert.equal(sha(bytes),build.wasmSha256);
const module=new WebAssembly.Module(bytes),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}});
const memory=new WebAssembly.Memory({initial:1024,maximum:16384,shared:true});
const imports={env:{memory},wasi_snapshot_preview1:wasi.wasiImport};
for(const x of WebAssembly.Module.imports(module)){
 imports[x.module]??={};if(x.kind==='function'&&!imports[x.module][x.name])imports[x.module][x.name]=()=>{throw Error('Unexpected platform call '+x.module+'.'+x.name);};
}
const instance=new WebAssembly.Instance(module,imports);wasi.initialize(instance);const c=instance.exports;
const f32=new Float32Array(1),u32=new Uint32Array(f32.buffer),float=b=>{u32[0]=b;return f32[0];},bits=f=>{f32[0]=f;return u32[0];};
const rows=[];
for(const r of reference.rows){
 const status=c.background_case(float(r.uvWord));assert.equal(status,r.status);
 assert.equal(c.draw_count(),1);assert.equal(r.draws.length,1);
 const vertices=Array.from({length:4},(_,i)=>Array.from({length:7},(_,j)=>j===4?c.vertex_color(i)>>>0:c.vertex_value(i,j)));
 const differences=[];
 for(let i=0;i<4;i++)for(let j=0;j<7;j++)if(j===4?vertices[i][j]!==r.draws[0][i][j]:bits(vertices[i][j])!==bits(r.draws[0][i][j]))differences.push({vertex:i,field:j,native:r.draws[0][i][j],cpp:vertices[i][j]});
 const expected=[null,null,null,null,null,null,null,null];
 for(const [kind,key,value]of r.events){const i=kind==='state'?({19:0,20:1,171:2,14:7})[key]:({6:3,5:4,1:5,2:6})[key];assert.notEqual(i,undefined);expected[i]=value;}
 const actual=expected.map((_,i)=>c.state_value(i));
 rows.push({name:r.name,vertices,differences,expectedMaterial:expected,actualMaterial:actual,materialExact:JSON.stringify(expected)===JSON.stringify(actual)});
}
const report={rows,bitExactVertices:rows.every(r=>r.differences.length===0),materialExact:rows.every(r=>r.materialExact),currentNormalProviders:141,controlledCameraOnly:true,actualGameOrFullFrameAccepted:false,completeGame:false};
writeFileSync(resolve(out,'comparison.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report));assert.ok(report.bitExactVertices&&report.materialExact);
