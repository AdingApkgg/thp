import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),dir='artifacts/th14/gpu-raster/',out=dir+'initial/';
const read=n=>readFileSync(resolve(root,n)),sha=b=>createHash('sha256').update(b).digest('hex');
const report=JSON.parse(read('docs/porting/th14-gpu-raster-browser-verified-oct11.json')),build=JSON.parse(read(dir+'build.json'));
const frozen={};
function save(original,bytes,hash){assert.equal(sha(bytes),hash,original);const path=out+original.replaceAll('/','_');mkdirSync(dirname(resolve(root,path)),{recursive:true});if(existsSync(resolve(root,path)))assert.equal(sha(read(path)),hash);else writeFileSync(resolve(root,path),bytes);frozen[original]={path,bytes:bytes.length,sha256:hash};}
for(const [path,row] of Object.entries(report.files))save(path,read(path),row.sha256);
for(const [path,hash] of Object.entries(build.sources)){
 let bytes=read(path);
 if(path.endsWith('/Renderer.cpp'))bytes=read(dir+'Renderer-before-alpha-fix.cpp');
 if(path.endsWith('/Renderer.hpp'))bytes=Buffer.from(bytes.toString().replace(/    const float\* alpha_boundaries\(\)const\{return alphaBoundaries.data\(\);\}\r?\n/,'').replace(/    std::array<float,256> alphaBoundaries\{\};\r?\n/,''));
 save(path,bytes,hash);
}
const originalReport=read('docs/porting/th14-gpu-raster-browser-verified-oct11.json');save('docs/porting/th14-gpu-raster-browser-verified-oct11.json',originalReport,sha(originalReport));
writeFileSync(resolve(root,out+'report.json'),JSON.stringify({passed:true,completeGame:false,nativeEquivalent:false,report,frozen},null,2)+'\n');
console.log(JSON.stringify({passed:true,frozenFiles:Object.keys(frozen).length,path:out+'report.json'}));
