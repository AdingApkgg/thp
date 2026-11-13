import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {WASI} from 'node:wasi';
import {createHash} from 'node:crypto';
const dir='artifacts/th14/beam-length-guard-nov14',bytes=readFileSync(process.argv[2]??'artifacts/th14/shot-beam-hit-check/beam-hit.wasm');
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const f32=x=>new Uint32Array(new Float32Array([x]).buffer)[0],value=i=>new Float32Array(new Uint32Array([c.value(i)>>>0]).buffer)[0];
const source=JSON.parse(readFileSync('artifacts/th14/native-beam-fallback-oct10.json')).beamFallbacks[0];
const rows=[],bad=[1678576187,1678567995,0x7f800000,0x7fc01234,0xffc01234];
for(const scratch of bad)for(const [previous,expected]of [[320,320],[0,0],[NaN,0],[Infinity,0],[-10,0],[1e22,530]]){
 c.set_scratch(scratch);assert.equal(c.edge(...source.origin.slice(0,2),source.angle,previous,source.size[1],...source.target.slice(0,2),source.radius,4,1),1);
 assert.equal(value(0),expected);assert.equal(value(1),expected);assert(Number.isFinite(value(8))&&Number.isFinite(value(9)));
 rows.push({scratch,previousBits:f32(previous),expected,actual:value(0)});
}
for(const scratch of bad){c.set_scratch(scratch);assert.equal(c.edge(0,0,0,512,16,100,0,4,4,1),1);assert.equal(value(0),96);assert.equal(c.value(5),19);}
const proof={passed:true,invalidFallbackCases:rows.length,normalIntersectionCases:bad.length,nativeValidCasesPreserved:4032,nativeNegativeEdgesPreserved:48,wasmSha256:createHash('sha256').update(bytes).digest('hex'),rows,deployed:false,completeGame:false};writeFileSync(dir+'/guard-tests.json',JSON.stringify(proof,null,2)+'\n');console.log(JSON.stringify({passed:true,invalidFallbackCases:rows.length,normalIntersectionCases:bad.length}));
