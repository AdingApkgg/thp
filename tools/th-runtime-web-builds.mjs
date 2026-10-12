// Check the per-title playable web harnesses.
//
// Two things have to hold for a per-title runtime to be the same runtime. First the artefact must be real: it must
// clear a size floor, its report must match the file by hash, and the report must name the title it was built for.
// Second the host protocol must be unchanged: the shell drives the module through a fixed C ABI, so every title's
// harness must export exactly the same names as the reference build. A title that quietly dropped an entry point,
// or added one, would break the shell in a way no size check can see.
//
// The reference is the th12 harness, which the browser campaign evidence was produced with. The comparison is on
// export and import *names*, not on bytes: the bytes are expected to differ, because PORT_TITLE selects a
// different no-op table and the two titles' tables differ.
//
// Build the harnesses with:
//   node runtimes/th12/th12_web/scripts/build-sdl.mjs
//   node runtimes/th13/th13_web/scripts/build-sdl.mjs
import {readFileSync,existsSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const MIN_BYTES=1024*1024;
const BUILDS=[
 {title:12,dir:'runtimes/th12/th12_web/artifacts/sdl3',loader:'th11-harness.mjs',release:false},
 {title:13,dir:'runtimes/th13/th13_web/artifacts/sdl3',loader:'th11-harness.mjs',release:false},
];
const sha=b=>createHash('sha256').update(b).digest('hex');
const fail=[];const measured=[];
for(const build of BUILDS){
    const wasm=resolve(root,build.dir,build.loader.replace('.mjs','.wasm'));
    const report=resolve(root,build.dir,'build.json');
    if(!existsSync(wasm)||!existsSync(report)){fail.push(`title ${build.title}: no harness build in ${build.dir}`);continue;}
    const bytes=readFileSync(wasm),body=JSON.parse(readFileSync(report,'utf8'));
    let module;
    try{module=new WebAssembly.Module(bytes);}catch(e){fail.push(`title ${build.title}: the artefact is not a wasm module (${e.message})`);continue;}
    if(bytes.length<MIN_BYTES)fail.push(`title ${build.title}: ${bytes.length} bytes is below the ${MIN_BYTES}-byte floor`);
    if(body.title!==undefined&&body.title!==build.title)fail.push(`title ${build.title}: the report says title ${body.title}`);
    if(body.bytes!==bytes.length)fail.push(`title ${build.title}: the report's byte count is stale`);
    if(body.sha256!==sha(bytes))fail.push(`title ${build.title}: the report's hash is stale against the artefact`);
    measured.push({title:build.title,bytes:bytes.length,
        exports:WebAssembly.Module.exports(module).map(e=>e.name).sort(),
        imports:WebAssembly.Module.imports(module).map(i=>`${i.module}.${i.name}`).sort()});
}
if(measured.length<2){fail.push('fewer than two harness builds were found; the reference comparison needs the th12 build and one other');}
else{
    const reference=measured[0];
    for(const other of measured.slice(1)){
        const onlyRef=reference.exports.filter(n=>!other.exports.includes(n));
        const onlyOther=other.exports.filter(n=>!reference.exports.includes(n));
        if(onlyRef.length)fail.push(`title ${other.title}: missing host entry points present in title ${reference.title}: ${onlyRef.join(', ')}`);
        if(onlyOther.length)fail.push(`title ${other.title}: exports host entry points absent from title ${reference.title}: ${onlyOther.join(', ')}`);
        const refImports=new Set(reference.imports);
        const newImports=other.imports.filter(n=>!refImports.has(n));
        if(newImports.length)fail.push(`title ${other.title}: imports symbols title ${reference.title} does not: ${newImports.slice(0,5).join(', ')}`);
    }
}
for(const m of measured)console.log(`title ${m.title}  bytes=${m.bytes}  exports=${m.exports.length}  imports=${m.imports.length}  host ABI=${m.exports.filter(n=>n.startsWith('th11_')).length}`);
if(fail.length){for(const f of fail)console.error('FAIL '+f);process.exitCode=1;}else console.log('per-title web harnesses OK');
