// Response-only local preview policy. Frozen resources and the mixer stay intact.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {resolve,relative,isAbsolute,extname} from 'node:path';
import {fileURLToPath} from 'node:url';
export const root=resolve(import.meta.dirname,'..');
export const digest=b=>createHash('sha256').update(b).digest('hex');
const quiet=readFileSync(resolve(root,'tools/th14-local-quiet-audio.js'));
assert.equal(digest(quiet),'216745e0d5459c0546e3fed01866092e67f40c383380dd47c5aafa5bac4a134c');
export const quietRoute='/__workspace/quiet-audio.js';
const worker=Buffer.from("// local preview passthrough; no cache or save deletion\nself.addEventListener('install',()=>self.skipWaiting());\nself.addEventListener('activate',e=>e.waitUntil(self.clients.claim()));\n");
export function inside(base,path){const name=relative(base,path);assert(name&&!isAbsolute(name)&&name!=='..'&&!name.startsWith('../')&&!name.startsWith('..\\'),'Path outside preview root');return path;}
export function options(argv,allowed=[]){
 const value={port:8208,sound:false},seen=new Set();
 for(let i=0;i<argv.length;i++){
  assert(!seen.has(argv[i]),'Duplicate option');seen.add(argv[i]);
  if(argv[i]==='--sound'){value.sound=true;continue;}
  assert(['--port',...allowed].includes(argv[i])&&argv[i+1]&&!argv[i+1].startsWith('--'),'Unknown or missing option');
  const key=argv[i].slice(2);value[key]=argv[++i];
 }
 value.port=Number(value.port);assert(Number.isInteger(value.port)&&value.port>=1024&&value.port<=65535,'Invalid port');return value;
}
export function injectHtml(bytes,sound=false){
 if(sound)return bytes;
 const html=bytes.toString('utf8'),tag='<script src="'+quietRoute+'"></script>';
 if(html.includes(tag))return bytes;
 const head=/<head\b[^>]*>/i,htmlStart=/<html\b[^>]*>/i;
 assert(head.test(html)||htmlStart.test(html),'HTML insertion point required');
 return Buffer.from(html.replace(head.test(html)?head:htmlStart,match=>match+tag));
}
const types={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.mjs':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json; charset=utf-8','.wasm':'application/wasm','.png':'image/png','.svg':'image/svg+xml','.jpg':'image/jpeg','.webp':'image/webp','.ico':'image/x-icon','.woff':'font/woff','.woff2':'font/woff2','.flac':'audio/flac','.ogg':'audio/ogg'};
export function handler(files,settings){
 assert(files instanceof Map);
 return (req,res)=>{
  for(const [key,value]of Object.entries({'Cross-Origin-Opener-Policy':'same-origin','Cross-Origin-Embedder-Policy':'require-corp','Cross-Origin-Resource-Policy':'same-origin','Cache-Control':'no-store'}))res.setHeader(key,value);
  try{
   if(!['GET','HEAD'].includes(req.method))return res.writeHead(405).end();
   const path=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
   let bytes,type;
   if(path===quietRoute){if(settings.sound)return res.writeHead(404).end();bytes=quiet;type=types['.js'];}
   else{
    const entry=files.get(path);if(!entry)return res.writeHead(404).end();
    const original=entry.bytes??readFileSync(entry.path);
    if(entry.length!==undefined)assert.equal(original.length,entry.length,'Frozen length changed');
    if(entry.sha256)assert.equal(digest(original),entry.sha256,'Frozen resource changed');
    type=types[extname(entry.name??entry.path)]??'application/octet-stream';
    bytes=path==='/app-shell-sw.js'?worker:type===types['.html']?injectHtml(original,settings.sound):original;
   }
   res.setHeader('Content-Type',type);res.setHeader('Content-Length',bytes.length);
   return res.writeHead(200).end(req.method==='HEAD'?undefined:bytes);
  }catch{return res.writeHead(500).end('Local preview integrity failure');}
 };
}
export function isMain(url){return !!process.argv[1]&&resolve(process.argv[1])===fileURLToPath(url);}
