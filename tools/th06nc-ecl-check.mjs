// Produce an auditable structural census without claiming instruction execution.
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {readEcl} from '../shared/th06nc/ecl.mjs';
const root=new URL('../',import.meta.url);
const sha=b=>createHash('sha256').update(b).digest('hex');
const manifest=JSON.parse(readFileSync(new URL('artifacts/th06nc/scripts.json',root),'utf8'));
const files=[];
for(const file of manifest.filter(f=>f.name.endsWith('.ecl'))){
 const bytes=readFileSync(file.path);
 if(sha(bytes)!==file.sha256)throw Error(`Resource changed: ${file.path}`);
 const ecl=readEcl(bytes),ops={},timelineOps={};
 for(const sub of ecl.subroutines)for(const ins of sub.instructions)ops[ins.opcode]=(ops[ins.opcode]??0)+1;
 for(const sub of ecl.timelines.filter(Boolean))for(const ins of sub.instructions)timelineOps[ins.opcode]=(timelineOps[ins.opcode]??0)+1;
 files.push({name:file.name,sha256:file.sha256,subroutines:ecl.subroutines.length,
  instructions:Object.values(ops).reduce((a,b)=>a+b,0),timelineInstructions:Object.values(timelineOps).reduce((a,b)=>a+b,0),ops,timelineOps});
}
if(files.length!==7)throw Error('Expected all seven TH06nc ECL files');
const report={scope:'Structural parsing only; instruction semantics and gameplay are unverified.',
 readerSha256:sha(readFileSync(new URL('shared/th06nc/ecl.mjs',root))),files};
writeFileSync(new URL('docs/porting/th06nc-ecl.json',root),JSON.stringify(report,null,2)+'\n');
console.log(`${files.length} ECL files: ${files.reduce((n,f)=>n+f.subroutines,0)} subroutines, ${files.reduce((n,f)=>n+f.instructions,0)} commands, ${files.reduce((n,f)=>n+f.timelineInstructions,0)} timeline commands.`);
