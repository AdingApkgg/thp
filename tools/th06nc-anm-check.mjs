import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {readAnm} from '../shared/th06nc/anm.mjs';
const root=new URL('../',import.meta.url),sha=b=>createHash('sha256').update(b).digest('hex');
const manifest=JSON.parse(readFileSync(new URL('artifacts/th06nc/scripts.json',root))),files=[],ops={};
for(const ref of manifest.filter(f=>f.name.endsWith('.anm'))){
 const b=readFileSync(ref.path);if(sha(b)!==ref.sha256)throw Error('Resource changed: '+ref.name);
 const a=readAnm(b);
 for(const s of a.scripts)for(const i of s.instructions){const key=`${i.opcode}:${i.args.length}`;ops[key]=(ops[key]??0)+1;}
 files.push({archive:ref.archive,name:ref.name,sha256:ref.sha256,textureName:a.textureName,width:a.width,height:a.height,sprites:a.sprites.length,scripts:a.scripts.length,instructions:a.scripts.reduce((n,s)=>n+s.instructions.length,0)});
}
const report={scope:'ANM structural loading only; instructions and extra sprite fields not assigned unverified semantics.',readerSha256:sha(readFileSync(new URL('shared/th06nc/anm.mjs',root))),completeGame:false,files,opcodeAndArgumentBytes:ops};
writeFileSync(new URL('docs/porting/th06nc-anm-verified.json',root),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({files:files.length,sprites:files.reduce((n,f)=>n+f.sprites,0),scripts:files.reduce((n,f)=>n+f.scripts,0),instructions:files.reduce((n,f)=>n+f.instructions,0)}));
