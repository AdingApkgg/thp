import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';
import {resolve,extname} from 'node:path';
const root=resolve(import.meta.dirname,'..'),out=resolve(root,'artifacts/th14/gpu-world');
const files=new Map([['/',resolve(root,'tools/th14-gpu-world-float.html')],...['native.json','native.rgba32f'].map(n=>['/'+n,resolve(root,'artifacts/th14/gpu-world-float',n)])]);
for(const name of ['float-r','float-g','float-b','float-a'])for(const file of ['gpu.mjs','gpu.wasm','build.json'])files.set('/variants/'+name+'/'+file,resolve(out,'variants',name,file));
createServer(async(req,res)=>{try{const file=files.get(new URL(req.url,'http://localhost').pathname);if(!file||!['GET','HEAD'].includes(req.method)){res.writeHead(404).end();return;}const bytes=await readFile(file);res.writeHead(200,{'Content-Type':({'.html':'text/html;charset=utf-8','.mjs':'text/javascript','.wasm':'application/wasm','.json':'application/json'})[extname(file)]||'application/octet-stream','Content-Length':bytes.length,'Cache-Control':'no-store'});res.end(req.method==='HEAD'?undefined:bytes);}catch(e){res.writeHead(500).end(e.message);}}).listen(8143,'127.0.0.1',()=>console.log('TH14 fog float diagnostic http://127.0.0.1:8143/'));
