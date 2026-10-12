import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),proof=JSON.parse(readFileSync(resolve(root,'docs/porting/th14-launcher-preview-prepared-oct11.json'))),site=resolve(proof.site),port=Number(process.argv[2]??8135),sha=b=>createHash('sha256').update(b).digest('hex');
assert.equal(proof.passed,true);assert(site.startsWith(resolve(root,'runtimes/th14/th14_web/artifacts')+'\\'));
const files={...proof.files,'files.json':{sha256:sha(readFileSync(resolve(site,'files.json')))}};
const types={html:'text/html; charset=utf-8',js:'text/javascript; charset=utf-8',mjs:'text/javascript; charset=utf-8',css:'text/css; charset=utf-8',json:'application/json; charset=utf-8',wasm:'application/wasm',png:'image/png',svg:'image/svg+xml',jpg:'image/jpeg',webp:'image/webp',ico:'image/x-icon',woff:'font/woff',woff2:'font/woff2',flac:'audio/flac'};
createServer((req,res)=>{
 res.setHeader('Cross-Origin-Opener-Policy','same-origin');res.setHeader('Cross-Origin-Embedder-Policy','require-corp');res.setHeader('Cross-Origin-Resource-Policy','same-origin');res.setHeader('Cache-Control','no-store');
 try{
  if(!['GET','HEAD'].includes(req.method)){res.writeHead(405);res.end();return;}
  const url=new URL(req.url,'http://127.0.0.1'),name=decodeURIComponent(url.pathname).slice(1)||'index.html';
  if(!Object.hasOwn(files,name)){res.writeHead(404);res.end('Not found');return;}
  const bytes=readFileSync(resolve(site,name));assert.equal(sha(bytes),files[name].sha256,'changed prepared site '+name);if(files[name].bytes!=null)assert.equal(bytes.length,files[name].bytes);
  res.setHeader('Content-Type',types[name.split('.').at(-1)]??'application/octet-stream');res.setHeader('Content-Length',bytes.length);res.writeHead(200);res.end(req.method==='HEAD'?undefined:bytes);
 }catch(error){console.error(error.message);res.writeHead(500);res.end('Prepared site integrity failure');}
}).listen(port,'127.0.0.1',()=>console.log(`TH14 real Launcher preview: http://127.0.0.1:${port}/ (${Object.keys(proof.files).length} verified files)`));
