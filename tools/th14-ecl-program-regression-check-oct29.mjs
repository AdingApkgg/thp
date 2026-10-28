import {readFile,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
const args=process.argv.slice(2);assert.equal(args.length,2);assert.equal(args[0],'--home');const home=resolve(args[1]),sha=b=>createHash('sha256').update(b).digest('hex');
const buildRaw=await readFile(resolve(home,'build.json')),build=JSON.parse(buildRaw),archive=new Uint8Array(await readFile('H:/Games/th/14/th14.dat'));
assert.equal(sha(archive),'57d84a5cbe82460931cca26f090a0fde7aef180889ce5bfe8315851fc97b0233');
const modules=[],rows=[];let report;
try{
  for(const variant of ['published','current']){
    const metadata=build.builds[variant];for(const [name,field]of [['fixture.mjs','loaderSha256'],['fixture.wasm','wasmSha256']])assert.equal(sha(await readFile(resolve(home,variant,name))),metadata[field]);
    const {default:create}=await import(pathToFileURL(resolve(home,variant,'fixture.mjs'))),m=await create(),pointer=m._malloc(archive.length);m.HEAPU8.set(archive,pointer);assert.equal(m._fixture_open(pointer,archive.length),24);modules.push({m,pointer});
  }
  for(let index=0;index<24;++index){const names=modules.map(({m})=>m.UTF8ToString(m._fixture_name(index)));assert.equal(names[0],names[1]);const snapshots=[];
    for(const {m}of modules){const bytes=new TextEncoder().encode(names[0]+'\0'),p=m._malloc(bytes.length);m.HEAPU8.set(bytes,p);let output;
      try{output=m._fixture_program(p);}finally{m._free(p);}assert(output,m.UTF8ToString(m._fixture_error()));snapshots.push(m.HEAPU8.slice(output,output+m._fixture_size()));
    }
    assert.equal(Buffer.compare(snapshots[0],snapshots[1]),0,names[0]);rows.push({name:names[0],snapshotBytes:snapshots[0].length,snapshotSha256:sha(snapshots[0]),orderedFilesDefinitionsReadSequenceAnimationsAndEveryNameLookupEqual:true});
  }
  report={passed:true,cases:rows.length,rows,publishedBase:build.publishedBase,directSnapshotBytesCompared:rows.reduce((n,r)=>n+r.snapshotBytes,0),publishedVsCurrentActualCpp:true,allDefinitionNamesLookedUp:true,definitionPointersComparedAsOwnedFileAndOffset:true,buildSha256:sha(buildRaw),checkerSha256:sha(await readFile(fileURLToPath(import.meta.url))),completeGame:false,nativeEquivalent:false};
}catch(error){report={passed:false,error:String(error.stack??error),rows,completeGame:false,nativeEquivalent:false};process.exitCode=1;}
finally{for(const {m,pointer}of modules)m._free(pointer);}
await writeFile(resolve(home,'check.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify(Object.fromEntries(Object.entries(report).filter(([name])=>name!=='rows'))));
