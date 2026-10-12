import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';
import {resolve,extname} from 'node:path';
const root=resolve(import.meta.dirname,'..'),out=resolve(root,'artifacts/th14/gpu-alpha-depth');
const files=new Map([['/',resolve(root,'tools/th14-gpu-alpha-depth.html')],...['gpu.mjs','gpu.wasm','native.json','native.bgra','build.json'].map(n=>['/'+n,resolve(out,n)])]);
createServer(async(req,res)=>{try{const path=new URL(req.url,'http://localhost').pathname,file=files.get(path);if(!file||!['GET','HEAD'].includes(req.method)){res.writeHead(404).end();return;}const bytes=await readFile(file);res.writeHead(200,{'Content-Type':({'.html':'text/html;charset=utf-8','.mjs':'text/javascript','.wasm':'application/wasm','.json':'application/json'})[extname(file)]||'application/octet-stream','Content-Length':bytes.length,'Cache-Control':'no-store'});res.end(req.method==='HEAD'?undefined:bytes);}catch(e){res.writeHead(500).end(e.message);}}).listen(8140,'127.0.0.1',()=>console.log('TH14 GPU alpha fixture http://127.0.0.1:8140/'));
