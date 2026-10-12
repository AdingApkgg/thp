import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {WASI} from 'node:wasi';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),bytes=readFileSync(resolve(root,'artifacts/th14/startup-session/startup.wasm')),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const string=p=>{const b=new Uint8Array(c.memory.buffer);return new TextDecoder().decode(b.subarray(p,b.indexOf(0,p)));};
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'),'utf8')),archive=readFileSync(target.dataArchives['th14.dat'].path),p=c.allocate(archive.length);new Uint8Array(c.memory.buffer,p,archive.length).set(archive);assert.equal(c.open_archive(p,archive.length),1);
mkdirSync(resolve(root,'artifacts/th14/spell-ecl'),{recursive:true});
for(let stage=1;stage<=7;++stage){const p=c.archive_spell_source(stage),n=c.archive_spell_size(stage);assert.ok(p&&n);writeFileSync(resolve(root,`artifacts/th14/spell-ecl/st0${stage}.ecl`),Buffer.from(new Uint8Array(c.memory.buffer,p,n)));}
const table=JSON.parse(readFileSync(resolve(root,'artifacts/th14/spell-menu-table-native.json'),'utf8'));
assert.equal(table.executableSha256,'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353');
console.log('Extracted actual stage ECL scripts');
const first=process.argv.includes('--all')?Array.from({length:120},(_,id)=>id):[0,26,108];
const rows=[];
const loadouts=process.argv.includes('--six-loadouts')?[0,1,2,3,4,5]:[0];
outer:for(const selection of loadouts)for(const id of first){let stage=0;for(let n=0;n<7;++n)for(let r=0;r<table.rows[n];++r){const choices=table.table[n].slice(r*5,r*5+5);if(choices.slice(0,choices.findIndex(v=>v<0)).includes(id))stage=n+1;}
 const difficulty=table.difficulty[id];assert.ok(stage>=1&&stage<=7);
 let error='',frames=0;try{assert.equal(c.spell_session_begin(stage,id,selection,difficulty),1,string(c.error()));assert.deepEqual(Array.from({length:7},(_,n)=>c.spell_session_value(n)),[id,0,0,400,id,32,2]);for(;frames<900;++frames){if(!c.tick(0)||!c.draw())throw Error(string(c.error()));if(c.phase()!==1)break;}}catch(e){error=e.message;}
 const result={id,stage,selection,difficulty,frames,phase:c.phase(),values:Array.from({length:10},(_,n)=>c.spell_session_value(n)),error};rows.push(result);console.log(JSON.stringify(result));if(error)break outer;
}
const sha=b=>createHash('sha256').update(b).digest('hex'),passed=rows.length===first.length*loadouts.length&&rows.every(r=>!r.error);
const report={passed,completeGame:false,nativeEquivalent:false,cases:rows.length,expectedCases:first.length*loadouts.length,loadouts,frameLimit:900,wasmSha256:sha(bytes),nativeExecutableSha256:table.executableSha256,archiveSha256:sha(archive),rows,scope:'Diagnostic actual original ECL entry, live production update/draw, no input up to 900 frames or natural death. No artificial invulnerability/firepower, no retail gameplay comparison, no complete capture/retry/replay proof.',sources:Object.fromEntries(['runtimes/th12/th12_web/cpp/game/GameBattle.cpp','runtimes/th12/th12_web/cpp/game/GameBattle.hpp','runtimes/th12/th12_web/cpp/game/GameSession.cpp','runtimes/th12/th12_web/cpp/game/EnemyTh14Commands.cpp','runtimes/th12/th12_web/tests/cpp/th14-startup-fixture.cpp','tools/th14-spell-session-probe.mjs'].map(n=>[n,sha(readFileSync(resolve(root,n)))]))};
writeFileSync(resolve(root,'artifacts/th14/spell-session-probe-oct11.json'),JSON.stringify(report,null,2)+'\n');
if(!passed)process.exitCode=1;else console.log(`PASS ${rows.length} actual ECL spell entries (${loadouts.length} loadouts)`);
