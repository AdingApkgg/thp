import assert from 'node:assert/strict';
import {readFileSync as read,writeFileSync as write} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),home=resolve(process.argv[2]??resolve(root,'artifacts/th14/anm-camera-reference-oct24'));
const sha=b=>createHash('sha256').update(b).digest('hex'),nativeBytes=read(resolve(home,'native.json')),proof=JSON.parse(nativeBytes);
assert.equal(proof.toolSha256,sha(read(resolve(root,'tools/th14-anm-camera-reference-native-oct24.py'))));
assert.equal(proof.executableSha256,sha(read('H:/Games/th/14/th14.exe')));assert.equal(proof.rows.length,72);assert.equal(proof.instructionBytesPatched,0);
const floatBits=f=>{const b=Buffer.alloc(4);b.writeFloatLE(f);return b.readUInt32LE();},results={};
for(const label of ['before','after']){
 const bytes=read(resolve(home,label+'.wasm')),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports,differences=[];
 for(const row of proof.rows){row.inputBits.forEach((bits,i)=>c.input(i,bits));const actual=c.reference(floatBits(row.reference+row.fraction))>>>0;if(actual!==row.outputBits)differences.push({cameraCase:row.cameraCase,reference:row.reference,fraction:row.fraction,native:row.outputBits,portable:actual});}
 results[label]={wasmSha256:sha(bytes),cases:proof.rows.length,differenceCount:differences.length,differences};
}
assert(results.before.differenceCount>0);assert.equal(results.after.differenceCount,0);
const names=['runtimes/th12/th12_web/cpp/game/Stage.cpp','runtimes/th12/th12_web/cpp/game/GameBattle.cpp','runtimes/th12/th12_web/tests/cpp/th14-anm-camera-reference-fixture.cpp','tools/th14-anm-camera-reference-check-oct24.mjs'];
const report={passed:true,results,nativeProofSha256:sha(nativeBytes),sourceHashes:Object.fromEntries(names.map(n=>[n,sha(read(resolve(root,n)))])),scope:'Original46f770 getters10016..10021 versus real Stage::publish_camera and AnmVm::float_value. Camera input words are controlled;72 calls include nonzero eye offsets, fractional IDs, large-float rounding and signed zero. Old engine object control must fail. Camera generation, pixel and PCM equality not claimed.',completeGame:false,nativeEquivalent:false};
write(resolve(root,'docs/porting/th14-anm-camera-reference-verified-oct24.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:true,cases:proof.rows.length,oldObjectDifferences:results.before.differenceCount,currentObjectDifferences:results.after.differenceCount}));
