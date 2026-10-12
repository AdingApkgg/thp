// Loopback-only test harness for th13's web build. Same allowlist shape as th12's serve-sdl.mjs, with this title's
// own harness and archive and with the title-neutral parts of the host shared by path.
//
// What is shared and why:
//   - app/shell.mjs, frame-clock.mjs, style.css: the host shell drives the module through the same _th11_* ABI in
//     every title, so one shell serves all of them. The shell writes whatever archive it is given to /th11.dat,
//     and the C++ archive layer opens /th11.dat, so the file name is protocol, not a title.
//   - fonts: the baked glyphs are rasterised from the Windows font faces, not from the game's data, so th13 uses
//     the same set until a title-specific bake is wanted.
//   - music: th13's own thbgm.dat has not been encoded yet, so this server serves the shared th12 tracks by
//     default as a stand-in. A browser boot is a claim about the runtime, not about the audio; --music=<dir> or
//     TH13_MUSIC points it at th13's own directory once prepare-music.py has produced one.
//
// The archive is read straight from the retail install, encrypted, exactly as the original does.
import {createServer} from 'node:http';
import {readFile,readdir,stat} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {resolve,dirname,extname} from 'node:path';

const root=fileURLToPath(new URL('../',import.meta.url));            // runtimes/th13/th13_web
const shared=resolve(root,'../../th12/th12_web');                   // shell, fonts, stand-in music
const target=JSON.parse(await readFile(resolve(root,'../target.json'),'utf8'));
if(target.game!=='th13')throw Error(`runtimes/th13/target.json says game=${target.game}`);
const argOf=name=>{const at=process.argv.indexOf('--'+name);return at<0?null:process.argv[at+1];};
const port=Number(argOf('port')||process.env.TH13_PORT||8114);
const buildDir=resolve(root,process.env.TH13_OUTPUT||'artifacts/sdl3');
// TH13's own tracks, once prepare-music-th13.py has written them: it is asked for one, and the
// shared TH12 directory is only there so a boot can run before the encode does. Both the shell's
// index and the runtime's /music/<stem>.ogg come from whichever directory is chosen here.
const ownMusic=resolve(root,'assets/sdl-native/music');
const usingOwnMusic=await stat(resolve(root,'assets/sdl-native/music-verification.json')).then(()=>true,()=>false);
const musicDir=resolve(argOf('music')||process.env.TH13_MUSIC||(usingOwnMusic?ownMusic:resolve(shared,'assets/sdl-native/music')));
console.log(`  music: ${musicDir}${argOf('music')||process.env.TH13_MUSIC||usingOwnMusic?'':" (TH13's own tracks are not encoded yet - this is TH12's stand-in)"}`);
const files=new Map([
 ['/', 'sdl-runtime/th13.html'],
 ['/app/style.css',null],
 ['/app/shell.mjs',null],
 ['/app/frame-clock.mjs',null],
 ['/th11-harness.mjs',null],
 ['/th11-harness.wasm',null],
 ['/th11.dat',null],
]);
const own=new Map([
 ['/',resolve(root,'sdl-runtime/th13.html')],
 ['/app/style.css',resolve(shared,'sdl-runtime/style.css')],
 ['/app/shell.mjs',resolve(shared,'sdl-runtime/shell-harness.mjs')],
 ['/app/frame-clock.mjs',resolve(shared,'sdl-runtime/frame-clock.mjs')],
 ['/th11-harness.mjs',resolve(buildDir,'th11-harness.mjs')],
 ['/th11-harness.wasm',resolve(buildDir,'th11-harness.wasm')],
 ['/th11.dat',target.dataArchives['th13.dat'].path],
]);
// The music index the shell reads: entries are {file}. th13 wants <stem>.ogg names; the stand-in keeps the shape.
// It sits beside the music directory, not inside it, which is how the th12 assets are laid out.
const musicIndex=resolve(dirname(musicDir),'music-verification.json');
files.set('/fonts-index.json',null);own.set('/fonts-index.json',resolve(shared,'assets/sdl-native/fonts/manifest.json'));
for(const name of ['font0.bin','font1.bin','font2.bin','font3.bin','cp932.bin','blend4444.bin']){
 files.set('/fonts/'+name,null);own.set('/fonts/'+name,resolve(shared,'assets/sdl-native/fonts',name));
}
files.set('/music-index.json',null);own.set('/music-index.json',musicIndex);
for(const name of await readdir(musicDir).catch(()=>[]))if(/^[a-z0-9_]+\.ogg$/.test(name)){
 files.set('/music/'+name,null);own.set('/music/'+name,resolve(musicDir,name));
}
const types={'.html':'text/html; charset=utf-8','.mjs':'text/javascript','.css':'text/css','.wasm':'application/wasm'};
const server=createServer(async(req,res)=>{
 try{
  if(!['GET','HEAD'].includes(req.method)){res.writeHead(405).end();return;}
  const path=new URL(req.url,'http://localhost').pathname;
  if(!files.has(path)){res.writeHead(404).end('not in the allowlist');return;}
  const name=own.get(path);
  const bytes=await readFile(name);
  res.writeHead(200,{'Content-Type':types[extname(name)]||'application/octet-stream','Content-Length':bytes.length,'Cache-Control':'no-store','Cross-Origin-Opener-Policy':'same-origin','Cross-Origin-Embedder-Policy':'require-corp'});
  res.end(req.method==='HEAD'?undefined:bytes);
 }catch(e){res.writeHead(500).end('Harness resource unavailable');console.error(e.message);}
});
server.listen(port,'127.0.0.1',async()=>{
 const size=(await stat(target.dataArchives['th13.dat'].path)).size;
 const tracks=Object.keys(Object.fromEntries(files)).filter(p=>p.startsWith('/music/')).length;
 console.log(`th13 SDL harness http://127.0.0.1:${port}/`);
 console.log(`  archive ${target.dataArchives['th13.dat'].path} (${(size/1048576).toFixed(1)} MB, encrypted, as shipped)`);
 console.log(`  music    ${musicDir} (${tracks} tracks${musicDir.includes('th12')?' - stand-in, th13 bgm not encoded yet':''})`);
});
