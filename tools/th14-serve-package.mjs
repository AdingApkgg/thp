// Copy beside package.json. Serve only the frozen inventory on loopback.
import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';
import {resolve,extname} from 'node:path';
import {createHash} from 'node:crypto';
const root=import.meta.dirname,manifest=JSON.parse(await readFile(resolve(root,'package.json'),'utf8'));
if(manifest.schema!=='th14-local-harness-package/1'||manifest.game!=='th14')throw Error('Invalid local TH14 package');
const at=process.argv.indexOf('--port'),port=at<0?8134:Number(process.argv[at+1]);if(!Number.isInteger(port)||port<1024||port>65535)throw Error('Invalid port');
const types={'.html':'text/html; charset=utf-8','.mjs':'text/javascript','.css':'text/css','.wasm':'application/wasm','.json':'application/json','.flac':'audio/flac'};
createServer(async(req,res)=>{try{
 if(!['GET','HEAD'].includes(req.method)){res.writeHead(405).end();return;}
 const path=new URL(req.url,'http://localhost').pathname,name=path==='/'?'index.html':path.slice(1),entry=Object.hasOwn(manifest.files,name)?manifest.files[name]:null;
 if(!entry||name.includes('..')||name.includes('\\')){res.writeHead(404).end();return;}
 const bytes=await readFile(resolve(root,'site',name));if(bytes.length!==entry.bytes||createHash('sha256').update(bytes).digest('hex')!==entry.sha256)throw Error('Frozen resource identity changed: '+name);
 res.writeHead(200,{'Content-Type':types[extname(name)]||'application/octet-stream','Content-Length':bytes.length,'Cache-Control':'no-store','Cross-Origin-Opener-Policy':'same-origin','Cross-Origin-Embedder-Policy':'require-corp'});res.end(req.method==='HEAD'?undefined:bytes);
}catch(e){console.error(e.message);res.writeHead(500).end('Frozen resource unavailable');}}).listen(port,'127.0.0.1',()=>console.log(`Frozen TH14 harness http://127.0.0.1:${port}/ (${manifest.musicTracks} lossless tracks)`));
