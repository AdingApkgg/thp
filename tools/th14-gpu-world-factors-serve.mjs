import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';
import {resolve,extname} from 'node:path';
const root=resolve(import.meta.dirname,'..'),out=resolve(root,'artifacts/th14/gpu-world');
const files=new Map([['/',resolve(root,'tools/th14-gpu-world-factors.html')],...['native.json','native.bgra'].map(n=>['/'+n,resolve(out,n)])]);
for(const name of ['control','scaled','mad','squared','exp2','prepared'])for(const file of ['gpu.mjs','gpu.wasm','build.json'])files.set('/variants/'+name+'/'+file,resolve(out,'variants',name,file));
createServer(async(req,res)=>{try{const path=new URL(req.url,'http://localhost').pathname,file=files.get(path);if(!file||!['GET','HEAD'].includes(req.method)){res.writeHead(404).end();return;}const bytes=await readFile(file);res.writeHead(200,{'Content-Type':({'.html':'text/html;charset=utf-8','.mjs':'text/javascript','.wasm':'application/wasm','.json':'application/json'})[extname(file)]||'application/octet-stream','Content-Length':bytes.length,'Cache-Control':'no-store'});res.end(req.method==='HEAD'?undefined:bytes);}catch(e){res.writeHead(500).end(e.message);}}).listen(8144,'127.0.0.1',()=>console.log('TH14 diagnostic fog variants http://127.0.0.1:8144/'));
