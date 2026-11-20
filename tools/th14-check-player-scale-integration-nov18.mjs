import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {pathToFileURL,fileURLToPath} from 'node:url';
import {resolve} from 'node:path';
const directory=process.argv.find(x=>x.startsWith('--workdir='))?.slice(10);if(!directory)throw Error('Use --workdir=<private prepared fixture directory>');
const R=fileURLToPath(new URL('../',import.meta.url)),Q=pathToFileURL(resolve(directory)+'/'),hash=b=>createHash('sha256').update(b).digest('hex');
const meta=JSON.parse(readFileSync(R+'docs/porting/th14-player-bullet-collision-verified.json'));
assert(meta.passed&&meta.cases===10800);
const referenceBytes=readFileSync(R+'artifacts/th14/player-bullet-collision-native.json'),proof=JSON.parse(referenceBytes),oldBytes=readFileSync(R+'artifacts/th14/player-bullet-collision-check/collision.wasm');assert.equal(hash(oldBytes),meta.wasmSha256);assert.equal(proof.executableSha256,meta.nativeExecutableSha256);assert.equal(proof.cases.length,10800);
const oldWasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),old=(await WebAssembly.instantiate(oldBytes,{wasi_snapshot_preview1:oldWasi.wasiImport})).instance;oldWasi.initialize(old);
const bytes=readFileSync(new URL('scale-collision.wasm',Q)),build=JSON.parse(readFileSync(new URL('scale-collision-build.json',Q)));assert.equal(hash(bytes),build.wasmSha256);
const module=new WebAssembly.Module(bytes),memory=new WebAssembly.Memory({initial:1024,maximum:16384,shared:true}),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),imports={env:{memory},wasi_snapshot_preview1:wasi.wasiImport};
const unexpected=[];
for(const i of WebAssembly.Module.imports(module))if(!imports[i.module]?.[i.name]){assert.equal(i.kind,'function');(imports[i.module]??={})[i.name]=()=>{unexpected.push(i.module+'.'+i.name);throw Error('Unexpected host boundary '+i.module+'.'+i.name);};}
const instance=new WebAssembly.Instance(module,imports);wasi.initialize(instance);const c=instance.exports;c.open_fixture();
const focusedBytes=readFileSync(new URL('native-scale-edges.json',Q)),focused=JSON.parse(focusedBytes);assert.equal(focused.executableSha256,proof.executableSha256);assert.equal(focused.instructionBytesPatched,0);
const floats=new Float32Array(1),bits=new Uint32Array(floats.buffer),toFloat=v=>{bits[0]=v;return floats[0];};let baseline=0,current=0,scaledCircles=0;const oldNegatives=[0,0],negatives=[0,0];
try{for(const [suite,rows]of [['legacy',proof.cases],['focused',focused.cases]])for(const [n,r]of rows.entries()){
 const a=r.input.map((v,i)=>i>=1&&i<=8?toFloat(v):v),expected=r.result[0]|(r.result[1]<<8);
 assert.equal(old.exports.test(...a),expected,'Pinned reference module '+n);baseline++;
 assert.equal(c.test(...a,0),expected,'Actual current PlayerFrame adapter '+n);current++;
 if(a[0]&&a[9]){scaledCircles++;for(let fault=1;fault<=2;fault++)if(c.test(...a,fault)!==expected)(suite==='legacy'?oldNegatives:negatives)[fault-1]++;}
}
 const scale=JSON.parse(readFileSync(R+'artifacts/th14/player-scale-native.json'));assert.equal(scale.executableSha256,proof.executableSha256);assert.equal(scale.updates.length,1080);
 for(const [index,r]of scale.updates.entries()){const p=c.current_bounds(r.result[0],r.result[12]);assert.deepEqual(Array.from(new Uint32Array(memory.buffer,p,24)),r.bounds,'Actual live update_bounds adapter '+index);}
}finally{c.close_fixture();}
writeFileSync(new URL('public-scale-collision-corpus-diagnostic.json',Q),JSON.stringify({baseline,current,scaledCircles,oldNegatives,negatives,unexpected},null,2)+'\n');
assert(scaledCircles>0&&negatives.every(n=>n>0));assert.equal(unexpected.length,0);
const q={passed:true,completeGame:false,silent:true,source:'Current verified PlayerFrame::collision and update_bounds adapters plus actual PlayerCollision circle/rectangle; synthetic SHT hitbox, player shape/state and native input cases are declared controlled boundaries. No Application/gameplay progression or native whole-game claim.',cases:current,pinnedPriorModuleCases:baseline,legacyCases:proof.cases.length,newNativeEdgeCases:focused.cases.length,scaledCircularCases:scaledCircles,currentBoundsCases:1080,currentBoundsWords:25920,legacyCorpusFaultDetection:{missingScale:oldNegatives[0],doubleScale:oldNegatives[1]},negativeControlMismatches:{missingScale:negatives[0],doubleScale:negatives[1]},priorWeakCorpusFailurePreserved:true,nativeExeSha256:proof.executableSha256,newNativeInstructionReferencesExecuted:true,nativeInstructionsPatched:0,nativeHitApplicationBoundary:'0x44f7a0 recorded sink, no code patch',newNativeGameProcessRun:false,newGameAssetCopies:0,newGameProvidersCompiled:0,providerObjectsVerified:build.providerObjectsVerified,legacyReferenceSha256:hash(referenceBytes),boundsNativeReferenceSha256:hash(readFileSync(R+'artifacts/th14/player-scale-native.json')),focusedNativeReferenceSha256:hash(focusedBytes),focusedNativeGeneratorSha256:hash(readFileSync(new URL('./th14-native-scaled-circle-edges-nov18.py',import.meta.url))),priorModuleSha256:hash(oldBytes),currentWasmSha256:hash(bytes),fixtureSha256:build.fixtureSha256,unexpectedHostCalls:unexpected};writeFileSync(new URL('public-scale-collision-qualified.json',Q),JSON.stringify(q,null,2)+'\n');console.log(JSON.stringify(q));
