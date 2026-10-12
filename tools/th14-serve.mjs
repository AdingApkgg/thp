// Local-only TH14 integration harness. It serves the user's original encrypted
// archive and this title's own music; no assets from another game stand in.
import {createServer} from 'node:http';
import {readFile,readdir} from 'node:fs/promises';
import {resolve,extname} from 'node:path';
import {fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('../',import.meta.url));
const rt=resolve(root,'runtimes/th14/th14_web'),shared=resolve(root,'runtimes/th12/th12_web');
const target=JSON.parse(await readFile(resolve(rt,'../target.json'),'utf8'));
if(target.game!=='th14')throw Error('TH14 target metadata required');
const at=process.argv.indexOf('--port'),port=at<0?8125:Number(process.argv[at+1]);
const build=resolve(rt,process.env.TH14_OUTPUT||'artifacts/sdl3');
const music=resolve(rt,'assets/sdl-native/music');
const files=new Map([
 ['/',process.argv.includes('--transition-proof')?resolve(root,'tools/th14-transition-proof.html'):resolve(rt,'sdl-runtime/th14.html')],
 ['/app/style.css',resolve(shared,'sdl-runtime/style.css')],
 ['/app/shell.mjs',resolve(shared,'sdl-runtime/shell-harness.mjs')],
 ['/app/frame-clock.mjs',resolve(shared,'sdl-runtime/frame-clock.mjs')],
 ['/app/keyboard.mjs',resolve(shared,'sdl-runtime/keyboard.mjs')],
 ['/app/browser-save-store.mjs',resolve(shared,'sdl-runtime/browser-save-store.mjs')],
 ['/th11-harness.mjs',resolve(build,'th11-harness.mjs')],
 ['/th11-harness.wasm',resolve(build,'th11-harness.wasm')],
 ['/th11.dat',target.dataArchives['th14.dat'].path],
 ['/fonts-index.json',resolve(rt,'assets/sdl-native/fonts/manifest.json')],
]);
for(const name of ['font0.bin','font1.bin','font2.bin','font3.bin','cp932.bin','blend4444.bin','font4.bin','font5.bin','font6.bin','font7.bin'])files.set('/fonts/'+name,resolve(rt,'assets/sdl-native/fonts',name));
const musicIndex=await readFile(resolve(music,'../music-verification.json')).catch(()=>Buffer.from('[]'));
for(const entry of JSON.parse(musicIndex))if(/^[a-z0-9_]+\.(?:ogg|flac)$/.test(entry.file))files.set('/music/'+entry.file,resolve(music,entry.file));
const types={'.html':'text/html; charset=utf-8','.mjs':'text/javascript','.css':'text/css','.wasm':'application/wasm','.json':'application/json'};
createServer(async(req,res)=>{
 try{
  if(!['GET','HEAD'].includes(req.method)){res.writeHead(405).end();return;}
  const path=new URL(req.url,'http://localhost').pathname,name=files.get(path);
  if(!name&&path!=='/music-index.json'){res.writeHead(404).end();return;}
  const bytes=path==='/music-index.json'?musicIndex:await readFile(name);
  res.writeHead(200,{'Content-Type':types[extname(name||path)]||'application/octet-stream','Content-Length':bytes.length,'Cache-Control':'no-store','Cross-Origin-Opener-Policy':'same-origin','Cross-Origin-Embedder-Policy':'require-corp'});
  res.end(req.method==='HEAD'?undefined:bytes);
 }catch(e){console.error(e.message);res.writeHead(500).end('Harness resource unavailable');}
}).listen(port,'127.0.0.1',()=>console.log(`TH14 integration harness http://127.0.0.1:${port}/ (${JSON.parse(musicIndex).length} original music tracks)`));
