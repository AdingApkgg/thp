import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';
import {resolve,extname} from 'node:path';
const root=resolve(import.meta.dirname,'..'),out=resolve(root,'artifacts/th14/gpu-stage-fog-rounding'),files=new Map([['/',resolve(out,'index.html')]]);
for(const name of ['native.json','native.bgra'])files.set('/stage/'+name,resolve(root,'artifacts/th14/gpu-stage-fog',name));
for(const name of ['depth-split','term-barrier','range-mul-rsq','vertex-clamp'])for(const file of ['gpu.mjs','gpu.wasm','build.json'])files.set('/stage/'+name+'/'+file,resolve(out,name,file));
createServer(async(req,res)=>{try{const p=files.get(new URL(req.url,'http://localhost').pathname);if(!p||!['GET','HEAD'].includes(req.method)){res.writeHead(404).end();return;}const b=await readFile(p);res.writeHead(200,{'Content-Type':({'.html':'text/html;charset=utf-8','.mjs':'text/javascript','.wasm':'application/wasm','.json':'application/json'})[extname(p)]||'application/octet-stream','Content-Length':b.length,'Cache-Control':'no-store'});res.end(req.method==='HEAD'?undefined:b);}catch(e){res.writeHead(500).end(e.message);}}).listen(8192,'127.0.0.1',()=>console.log('TH14 independent fog rounding http://127.0.0.1:8192/'));
