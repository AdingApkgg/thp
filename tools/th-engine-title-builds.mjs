// Check the per-title engine builds.
//
// The six titles share one engine, so a per-title build differs only in the tables the engine selects at compile
// time - the no-op table above all, since PortTitle.hpp is the only compile-time title switch. That gives the
// check a falsifiable shape: two titles whose no-op tables are byte-identical must produce byte-identical
// modules, and two titles whose tables differ must not. A build that ignores PORT_TITLE would make every module
// identical; a build that is stale would make a module disagree with its own report. Both are failures.
//
// The 256 KiB floor is the instrument lesson from section 47: a stripped, gc-sections link with no entry point and
// no exports produced a 220-byte module that every ordinary check would have called a success.
import {readFileSync,existsSync,readdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const runtime=resolve(root,'runtimes/th13/th13_web');
const shared=resolve(root,'runtimes/th12/th12_web');
const TITLES=[12,13,14,16,17,18],MIN_BYTES=256*1024;
const sha=b=>createHash('sha256').update(b).digest('hex');
const fail=[];
const noop=readFileSync(resolve(shared,'cpp/game/NoopOpcodes.hpp'),'utf8');
// The per-title no-op column: the bit table and the first/last bounds it is indexed with.
function column(title){
    const name='th'+title;
    const body=noop.match(new RegExp(`const uint8_t ${name}_bits\\[\\]=\\{(.*?)\\};`,'s'));
    const bounds=noop.match(new RegExp(`const uint16_t ${name}_first=0x([0-9a-f]+),${name}_last=0x([0-9a-f]+);`));
    if(!body||!bounds)fail.push(`NoopOpcodes.hpp has no complete column for title ${title}`);
    return{bits:body?body[1].replace(/\s+/g,''):'',first:bounds?.[1],last:bounds?.[2]};
}
const engineSources=readdirSync(resolve(shared,'cpp/game')).filter(n=>n.endsWith('.cpp')).length;
const measured=[];
for(const title of TITLES){
    const wasm=resolve(runtime,`artifacts/cpp/engine-th${title}.wasm`);
    const report=resolve(runtime,`artifacts/cpp/engine-th${title}-build.json`);
    if(!existsSync(wasm)||!existsSync(report)){fail.push(`title ${title}: no build (${wasm} or its report is missing)`);continue;}
    const bytes=readFileSync(wasm),body=JSON.parse(readFileSync(report,'utf8'));
    if(bytes.length<MIN_BYTES)fail.push(`title ${title}: ${bytes.length} bytes is below the ${MIN_BYTES}-byte floor - a module that cannot hold the engine is not a build`);
    if(body.title!==title)fail.push(`title ${title}: the report says title ${body.title}`);
    if(body.engineSources!==engineSources)fail.push(`title ${title}: the report was built from ${body.engineSources} sources, the engine has ${engineSources}`);
    if(body.sha256!==sha(bytes))fail.push(`title ${title}: the report's hash is stale against the artefact`);
    measured.push({title,bytes:bytes.length,sha:sha(bytes),column:column(title)});
}
for(const a of measured)for(const b of measured){
    if(a.title>=b.title)continue;
    const sameColumn=a.column.bits===b.column.bits&&a.column.first===b.column.first&&a.column.last===b.column.last;
    const sameModule=a.sha===b.sha;
    if(sameColumn&&!sameModule)fail.push(`titles ${a.title} and ${b.title} share one no-op table but built different modules`);
    if(!sameColumn&&sameModule)fail.push(`titles ${a.title} and ${b.title} built the same module from different no-op tables - PORT_TITLE is not reaching the build`);
}
if(!measured.length)fail.push('no per-title engine build was found');
for(const m of measured)console.log(`title ${String(m.title).padStart(2)}  bytes=${String(m.bytes).padStart(7)}  no-op 0x${m.column.first}..0x${m.column.last}  sha=${m.sha.slice(0,16)}`);
const shared_=measured.filter((m,i)=>measured.findIndex(n=>n.sha===m.sha)===i).length;
console.log(`titles ${measured.length}, distinct modules ${shared_}, engine sources ${engineSources}`);
if(fail.length){for(const f of fail)console.error('FAIL '+f);process.exitCode=1;}else console.log('per-title engine builds OK');
