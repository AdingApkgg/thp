// Loopback harness: own TH16 build, encrypted archive and original music conversions.
import {createServer} from 'node:http';
import {readFile,readdir} from 'node:fs/promises';
import {resolve,extname} from 'node:path';
import {fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('../',import.meta.url)),rt=resolve(root,'runtimes/th16/th16_web'),shared=resolve(root,'runtimes/th12/th12_web');
const target=JSON.parse(await readFile(resolve(rt,'../target.json'),'utf8'));
if(target.game!=='th16')throw Error('TH16 target metadata required');
const at=process.argv.indexOf('--port'),port=at<0?8128:Number(process.argv[at+1]);
if(!Number.isInteger(port)||port<1024||port>65535)throw Error('invalid port');
const build=resolve(rt,process.env.TH16_OUTPUT||'../artifacts/sdl3'),music=resolve(rt,'assets/sdl-native/music');
const files=new Map([
 ['/',resolve(rt,'sdl-runtime/th16.html')],
 ['/app/style.css',resolve(shared,'sdl-runtime/style.css')],
 ['/app/shell.mjs',resolve(shared,'sdl-runtime/shell-harness.mjs')],
 ['/app/frame-clock.mjs',resolve(shared,'sdl-runtime/frame-clock.mjs')],
 ['/th11-harness.mjs',resolve(build,'th16-harness.mjs')],
 ['/th11-harness.wasm',resolve(build,'th16-harness.wasm')],
 ['/th16-harness.wasm',resolve(build,'th16-harness.wasm')],
 ['/th11.dat',target.dataArchives['th16.dat'].path],
 ['/fonts-index.json',resolve(shared,'assets/sdl-native/fonts/manifest.json')],
 ['/music-index.json',resolve(music,'../music-verification.json')],
]);
for(const name of ['font0.bin','font1.bin','font2.bin','font3.bin','cp932.bin','blend4444.bin'])files.set('/fonts/'+name,resolve(shared,'assets/sdl-native/fonts',name));
for(const name of await readdir(music))if(/^[a-z0-9_]+\.ogg$/.test(name))files.set('/music/'+name,resolve(music,name));
const types={'.html':'text/html; charset=utf-8','.mjs':'text/javascript','.css':'text/css','.wasm':'application/wasm','.json':'application/json'};
createServer(async(req,res)=>{
 try{
  if(!['GET','HEAD'].includes(req.method)){res.writeHead(405).end();return;}
  const path=new URL(req.url,'http://localhost').pathname,name=files.get(path);if(!name){res.writeHead(404).end();return;}
  const bytes=await readFile(name);res.writeHead(200,{'Content-Type':types[extname(name)]||'application/octet-stream','Content-Length':bytes.length,'Cache-Control':'no-store','Cross-Origin-Opener-Policy':'same-origin','Cross-Origin-Embedder-Policy':'require-corp'});res.end(req.method==='HEAD'?undefined:bytes);
 }catch(e){console.error(e.message);res.writeHead(500).end('Harness resource unavailable');}
}).listen(port,'127.0.0.1',()=>console.log(`TH16 harness http://127.0.0.1:${port}/`));
