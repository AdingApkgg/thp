// Serve only the isolated current-source graphics fixture and frozen references.
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve,extname} from 'node:path';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),base=resolve(root,'artifacts/th14/stage-gpu-stream-replay'),out=resolve(root,'artifacts/th14/stage-current-sequential-clip-fe406-oct14');
const sha=b=>createHash('sha256').update(b).digest('hex'),read=p=>JSON.parse(readFileSync(p));
const nativeUV=read(resolve(base,'sampler-uv/native.json')),prepared=read(resolve(base,'prepared.json')),uvCases=nativeUV.frames.map(r=>({...r,role:'selected21',nativeSha256:r.fullFloatFrameSha256}));
const fullFrames=new Map(),fullBindings=[];
for(const [name,file] of [['world-uv','native.rgba32f'],['sampler-uv-worst','full.rgba32f'],['sampler-uv-strip','full.rgba32f']]){
 const nr=read(resolve(base,name,'native.json')),raw=readFileSync(resolve(base,name,file));
 for(const row of nr.frames){
  const bytes=name==='world-uv'?raw.subarray(row.offset,row.offset+row.bytes):raw;
  const expected=name==='world-uv'?row.sha256:row.fullFloatFrameSha256;assert.equal(sha(bytes),expected);
  const key=[row.stage,row.frame,row.originalDrawIndex].join('/');fullFrames.set(key,bytes);
  fullBindings.push({key,path:'artifacts/th14/stage-gpu-stream-replay/'+name+'/'+file,offset:row.offset||0,bytes:bytes.length,sha256:expected,reportPath:'artifacts/th14/stage-gpu-stream-replay/'+name+'/native.json',reportSha256:sha(readFileSync(resolve(base,name,'native.json')))});
  const found=uvCases.find(r=>[r.stage,r.frame,r.originalDrawIndex].join('/')===key);
  if(found)assert.equal(found.nativeSha256,expected);
  else{
   assert.equal(name,'world-uv');
   const points=row.frame===599?[[631,315]]:[[125,378],[114,214]];
   const samples=points.map(([x,y])=>({x,y,words:Array.from({length:4},(_,k)=>bytes.readUInt32LE((y*640+x)*16+k*4)),values:Array.from({length:4},(_,k)=>bytes.readFloatLE((y*640+x)*16+k*4))}));
   uvCases.push({...row,role:'depthAlwaysCoverageControl',nativeSha256:expected,samples});
  }
 }
}
const cases={cases:uvCases.map((r,i)=>({...r,index:i,nativeFullBytesAvailable:fullFrames.has([r.stage,r.frame,r.originalDrawIndex].join('/'))})),primaryCases:21,extraCoverageControls:2,nativeUVReportPath:'artifacts/th14/stage-gpu-stream-replay/sampler-uv/native.json',nativeUVReportSha256:sha(readFileSync(resolve(base,'sampler-uv/native.json'))),fullBindings};
writeFileSync(resolve(out,'uv-cases.json'),JSON.stringify(cases,null,2)+'\n');
const routes=new Map([['/',resolve(root,'tools/th14-stage-sequential-clip.html')],['/prepared.json',resolve(base,'prepared.json')],['/native-color.json',resolve(base,'native.json')],['/native-color.bgra',resolve(base,'native.bgra')],['/uv-cases.json',resolve(out,'uv-cases.json')]]);
for(const t of prepared.textures)routes.set('/'+t.file,resolve(base,t.file));
for(const mode of ['color','uv'])for(const file of ['gpu.mjs','gpu.wasm','build.json'])routes.set('/'+mode+'/'+file,resolve(out,mode,file));
const atomicEvidence=(p,b)=>{if(existsSync(p))assert.equal(sha(readFileSync(p)),sha(b),'Existing capture cannot be overwritten: '+p);else writeFileSync(p,b);};
const server=createServer(async(req,res)=>{try{
 const url=new URL(req.url,'http://127.0.0.1');
 if(req.method==='POST'){
  const match=/^\/capture\/(color|uv)\/(frame-[0-9]{3}\.(?:bgra|rgba32f)|report\.json)$/.exec(url.pathname);assert(match,'Restricted capture route');
  const [_,mode,file]=match,parts=[];let size=0;for await(const chunk of req){size+=chunk.length;assert(size<=6000000,'Capture size limit');parts.push(chunk);}const bytes=Buffer.concat(parts);
  if(file!=='report.json'){const i=Number(file.slice(6,9));assert(i>=0&&i<(mode==='color'?21:23));assert.equal(bytes.length,640*480*(mode==='color'?4:16));assert.equal(extname(file),mode==='color'?'.bgra':'.rgba32f');}
  else {const report=JSON.parse(bytes);assert.equal(report.mode,mode);assert.equal(report.reports.length,mode==='color'?21:23);}
  const dir=resolve(out,mode,'capture');mkdirSync(dir,{recursive:true});atomicEvidence(resolve(dir,file),bytes);res.writeHead(200,{'Content-Type':'application/json'}).end(JSON.stringify({saved:true,bytes:bytes.length,sha256:sha(bytes)}));return;
 }
 assert(['GET','HEAD'].includes(req.method));let bytes;
 const native=/^\/native-full\/([0-9]{3})$/.exec(url.pathname);
 if(native){const row=cases.cases[Number(native[1])];assert(row);bytes=fullFrames.get([row.stage,row.frame,row.originalDrawIndex].join('/'));assert(bytes,'No archived Native full buffer');}
 else {const p=routes.get(url.pathname);if(!p){res.writeHead(404).end();return;}bytes=readFileSync(p);}
 const ext=url.pathname==='/'?'.html':extname(url.pathname);res.writeHead(200,{'Content-Type':({'.html':'text/html;charset=utf-8','.mjs':'text/javascript','.wasm':'application/wasm','.json':'application/json'})[ext]||'application/octet-stream','Content-Length':bytes.length,'Cache-Control':'no-store'});res.end(req.method==='HEAD'?undefined:bytes);
 }catch(e){res.writeHead(500).end(e.stack||String(e));}});
server.listen(Number(process.env.TH14_SEQUENTIAL_CLIP_PORT||8245),'127.0.0.1',()=>console.log('Owned TH14 sequential CPU clip diagnostic at 127.0.0.1:'+(process.env.TH14_SEQUENTIAL_CLIP_PORT||8245)));
