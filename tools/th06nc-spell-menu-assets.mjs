import {openSync,readSync,closeSync,fstatSync,readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {openPkgl} from '../shared/th06nc/pkgl.mjs';
import {readAnm} from '../shared/th06nc/anm.mjs';
import {spellMenuAsset} from '../shared/th06nc/spell-practice-layout.mjs';

const target=JSON.parse(readFileSync('runtimes/th06nc/target.json')),sha=b=>createHash('sha256').update(b).digest('hex'),archiveName=spellMenuAsset.archive,fd=openSync(target.dataArchives[archiveName].path,'r'),evidence=JSON.parse(readFileSync('artifacts/th06nc/pkgl-python.json')).archives.find(a=>a.file===archiveName),files=[];
assert.equal(sha(readFileSync(target.executable)),target.sha256);
try{
 const archive=await openPkgl(async(offset,length)=>{const b=new Uint8Array(length);assert.equal(readSync(fd,b,0,length,offset),length);return b;},fstatSync(fd).size,archiveName);
 const extract=async(name,directory)=>{const entry=archive.entries.find(e=>e.name===name);assert.ok(entry,name);const bytes=await archive.readEntry(entry.index),hash=sha(bytes);assert.equal(hash,evidence.decoded.find(e=>e.name===name)?.sha256);mkdirSync(directory,{recursive:true});writeFileSync(directory+'/'+name,bytes);files.push({archive:archiveName,name,bytes:bytes.length,sha256:hash});return bytes;};
 const anm=await extract(spellMenuAsset.file,'runtimes/th06nc/artifacts/scripts/'+archiveName),resource=readAnm(anm);
 await extract(resource.textureName.split('/').at(-1).replace(/\.png$/,'.dds'),'runtimes/th06nc/artifacts/textures');
 const sources=['shared/th06nc/pkgl.mjs','shared/th06nc/anm.mjs','shared/th06nc/spell-practice-layout.mjs'];
 const report={scope:'Spell-menu ANM and referenced original DDS intake with independent PKGL hashes. Does not prove UI update/draw or pixel equivalence.',files,sourceSha256:Object.fromEntries(sources.map(p=>[p,sha(readFileSync(p))])),passed:true,completeGame:false,nativeEquivalent:false};writeFileSync('docs/porting/th06nc-spell-menu-assets-verified.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:true,files}));
}finally{closeSync(fd);}
