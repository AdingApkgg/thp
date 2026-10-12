// List a title's archive entry names in archive order, through the port's own decoder.
//
// This exists to derive a per-title resource table rather than guess it. th12's sample list is documented as
// ".data 0x4aea50, 49 consecutive pointers to .rdata se_*.wav strings, in the same order as th12.dat's
// archive", and `runtimes/th12/th12_web/cpp/game/SoundEffects.cpp` carries the names in that order. The same
// argument has to be made for the other five titles, and the archive half of it is this tool: given a title
// and a suffix it prints the matching entries in the order the archive holds them, so the order can be compared
// with the order of the strings and pointers inside that title's executable.
//
// Usage: node tools/th-archive-names.mjs <title> <pbg-version> [suffix]
import {readFileSync,existsSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {WASI} from 'node:wasi';
const here=dirname(fileURLToPath(import.meta.url));
const repo=resolve(here,'..');
const [title,version,suffix]=process.argv.slice(2);
if(!title||!version){console.error('usage: th-archive-names.mjs <title> <pbg-version> [suffix]');process.exit(2);}
const CORE=resolve(repo,'runtimes/th12/th12_web/artifacts/cpp/game-core-test.wasm');
// The target description is not in the same place for every title: th12 keeps it inside its runtime directory,
// th13..th18 keep it beside the runtime. Both are tried rather than assumed.
const targetCandidates=[resolve(repo,`runtimes/th${title}/th${title}_web/target.json`),resolve(repo,`runtimes/th${title}/target.json`)];
const targetPath=targetCandidates.find(p=>existsSync(p));
if(!targetPath){console.error(`no target.json for title ${title} in ${targetCandidates.join(' or ')}`);process.exit(2);}
const target=JSON.parse(readFileSync(targetPath,'utf8'));
const archivePath=process.env.TH_DAT??target.dataArchives[`th${title}.dat`].path;
const bytes=readFileSync(CORE);
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}});
const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});
wasi.initialize(instance);
const c=instance.exports;
const data=readFileSync(archivePath);
const p=c.allocate(data.length);
new Uint8Array(c.memory.buffer,p,data.length).set(data);
const archive=c.archive_create();
if(c.archive_open(archive,p,data.length,Number(version))!==1){
    console.error(`archive_open failed for th${title}.dat as version ${version}`);process.exit(1);
}
const count=c.archive_count(archive);
const names=[];
for(let n=0;n<count;n++){
    const ptr=c.archive_name(archive,n);
    const view=new Uint8Array(c.memory.buffer,ptr,256);
    const end=view.indexOf(0);
    const name=new TextDecoder().decode(view.subarray(0,end<0?256:end));
    if(suffix&&!name.endsWith(suffix))continue;
    names.push(name);
}
console.log(JSON.stringify({title:Number(title),version:Number(version),suffix:suffix??null,entries:count,matched:names.length,names},null,2));
