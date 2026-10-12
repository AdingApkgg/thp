import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';
import {resolve,extname} from 'node:path';
const root=resolve(import.meta.dirname,'..'),out=resolve(root,'artifacts/th14/gpu-screen-snap-production'),files=new Map();
const refs={shapes:['gpu-original-shapes','th14-gpu-original-shapes.html'],quads:['gpu-original-quads','th14-gpu-original-quads.html'],grid:['gpu-screen-grid','th14-gpu-screen-grid.html'],raster:['gpu-raster','th14-gpu-raster.html'],alpha:['gpu-alpha','th14-gpu-alpha.html'],'alpha-blend':['gpu-alpha-blend','th14-gpu-alpha-blend.html'],'alpha-depth':['gpu-alpha-depth','th14-gpu-alpha-depth.html']};
for(const [suite,[reference,page]] of Object.entries(refs)){
 files.set('/'+suite+'/',resolve(root,'tools',page));
 for(const n of ['gpu.mjs','gpu.wasm','build.json']){files.set('/'+suite+'/'+n,resolve(out,suite,n));if(suite==='grid')files.set('/grid/before/'+n,resolve(out,suite,n));}
 for(const n of ['native.json','native.bgra'])files.set('/'+suite+'/'+n,resolve(root,'artifacts/th14',reference,n));
}
for(const ext of ['json','bgra'])files.set('/alpha/native-low.'+ext,resolve(root,'artifacts/th14/gpu-alpha-low/native.'+ext));
createServer(async(req,res)=>{try{const path=new URL(req.url,'http://localhost').pathname,file=files.get(path);if(!file||!['GET','HEAD'].includes(req.method)){res.writeHead(404).end();return;}const bytes=await readFile(file);res.writeHead(200,{'Content-Type':({'.html':'text/html;charset=utf-8','.mjs':'text/javascript','.wasm':'application/wasm','.json':'application/json'})[extname(file)]||'application/octet-stream','Content-Length':bytes.length,'Cache-Control':'no-store'});res.end(req.method==='HEAD'?undefined:bytes);}catch(e){res.writeHead(500).end(e.message);}}).listen(8158,'127.0.0.1',()=>console.log('TH14 production subpixel correction GPU suites http://127.0.0.1:8158/shapes/'));
