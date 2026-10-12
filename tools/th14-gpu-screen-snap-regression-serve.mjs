import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';
import {resolve,extname} from 'node:path';
const root=resolve(import.meta.dirname,'..'),out=resolve(root,'artifacts/th14/gpu-screen-snap-regression'),files=new Map();
for(const suite of ['raster','alpha','alpha-blend','alpha-depth']){
 files.set('/'+suite+'/',resolve(root,'tools/th14-gpu-'+suite+'.html'));
 for(const n of ['gpu.mjs','gpu.wasm','build.json'])files.set('/'+suite+'/'+n,resolve(out,suite,n));
 for(const n of ['native.json','native.bgra'])files.set('/'+suite+'/'+n,resolve(root,'artifacts/th14/gpu-'+suite,n));
}
for(const ext of ['json','bgra'])files.set('/alpha/native-low.'+ext,resolve(root,'artifacts/th14/gpu-alpha-low/native.'+ext));
createServer(async(req,res)=>{try{const path=new URL(req.url,'http://localhost').pathname,file=files.get(path);if(!file||!['GET','HEAD'].includes(req.method)){res.writeHead(404).end();return;}const bytes=await readFile(file);res.writeHead(200,{'Content-Type':({'.html':'text/html;charset=utf-8','.mjs':'text/javascript','.wasm':'application/wasm','.json':'application/json'})[extname(file)]||'application/octet-stream','Content-Length':bytes.length,'Cache-Control':'no-store'});res.end(req.method==='HEAD'?undefined:bytes);}catch(e){res.writeHead(500).end(e.message);}}).listen(8156,'127.0.0.1',()=>console.log('TH14 screen-coordinate candidate regressions http://127.0.0.1:8156/raster/'));
