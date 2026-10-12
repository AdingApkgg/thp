import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const TITLE=17;
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,`artifacts/th${TITLE}/ecl-dispatch-check`);mkdirSync(out,{recursive:true});
// The independent side: resolve the shipped executable's two tables from its own bytes.
const resolved=execFileSync('py',['-3','tools/th-ecl-dispatch.py',`th${TITLE}`],{cwd:root,stdio:'pipe',windowsHide:true}).toString();
const agreement=/artifact agrees on (\d+) of (\d+) overlapping opcodes/.exec(resolved);
assert.ok(agreement,resolved.slice(0,200));
const fixture='tests/cpp/noop-title-fixture.cpp',source='cpp/game/NoopOpcodes.hpp',header='cpp/game/PortTitle.hpp';
const wasm=resolve(out,'noop.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),
 ['--target=wasm32-wasip1','-std=c++17','-O2','-fno-exceptions','-fno-rtti','-mexec-model=reactor',
  '-Wl,--no-entry','-Wl,--export-memory','-Wl,--export-all',`-DPORT_TITLE=${TITLE}`,fixture,'-o',wasm],
 {cwd:rt,stdio:'inherit',windowsHide:true,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out}});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),
      {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});
wasi.initialize(instance);const c=instance.exports;
assert.equal(c.noop_build_title(),TITLE,`the build must select TH${TITLE}`);
const document=JSON.parse(readFileSync(resolve(root,'docs/porting/noop-opcodes.json'),'utf8'));
const TITLES=[['th12',12],['th13',13],['th14',14],['th16',16],['th17',17],['th18',18]];
let checks=0,noops=0;
for(const[name,number]of TITLES){
 const row=document.titles[name],first=Number(row.first),last=Number(row.last);
 const expected=new Set(row.noops.map(Number));
 for(let op=first;op<=last;++op){const want=expected.has(op)?1:0;assert.equal(c.noop_probe(number,op),want,`${name} opcode 0x${op.toString(16)}`);++checks;if(want)++noops;}
 for(const op of [last+1,last+2,last+0x100,0xffff]){assert.equal(c.noop_probe(number,op),1,`${name} past the guard must be a no-op`);++checks;}
 for(let op=0;op<first;++op){assert.equal(c.noop_probe(number,op),0,`${name} 0x${op.toString(16)} is below the range`);++checks;}
}
// The discriminating claim: this build answers with its own title's column, and that column is not the
// same as another title's - otherwise the equality could hold for the wrong reason.
const mine=new Set(document.titles[`th${TITLE}`].noops.map(Number)),
      other=TITLES.find(([name])=>name!==`th${TITLE}`)[0],
      otherSet=new Set(document.titles[other].noops.map(Number));
let differs=0;
for(let op=0;op<=0x400;++op){if(c.noop_runtime(op)!==c.noop_probe(TITLE,op))assert.fail(`0x${op.toString(16)}: this build answered with another title's table`);if(mine.has(op)!==otherSet.has(op))++differs;++checks;}
assert.ok(differs>0,`the column of th${TITLE} must differ from ${other} somewhere for this claim to mean anything`);
const sha=b=>createHash('sha256').update(b).digest('hex');
const record=JSON.parse(readFileSync(resolve(root,`docs/porting/th${TITLE}-ecl-dispatch-verified.json`),'utf8'));
record.passed=true;
record.portSide={buildTitle:TITLE,query:'title_noop_opcode per title, runtime_noop_opcode for this build',
 column:'compared over every permitted opcode of all six titles, plus bands below and above each range',
 checks,noopAgreements:noops,differingOpcodesAgainst:other,buildAnswersWithOwnTitle:true,
 wasmSha256:sha(bytes),fixture,sourceHashes:Object.fromEntries([fixture,source,header].map(p=>[p,sha(readFileSync(resolve(rt,p)))]))};
record.nativeSide={resolver:'tools/th-ecl-dispatch.py (the executable bytes, independent of the tables)',agrees:Number(agreement[1]),overlapping:Number(agreement[2])};
record.scope='The dispatch record of section 294, now with the port compared against it: the no-op predicate of every title against the column derived from that title\'s own executable, and this build asserted to answer with its own title. Handler semantics stay outside.';
writeFileSync(resolve(root,`docs/porting/th${TITLE}-ecl-dispatch-verified.json`),JSON.stringify(record,null,2)+'\n');
console.log(`PASS: TH${TITLE} dispatch - ${checks} checks over six columns, ${noops} no-op agreements, resolver ${agreement[1]}/${agreement[2]}, this build selects TH${TITLE}.`);
