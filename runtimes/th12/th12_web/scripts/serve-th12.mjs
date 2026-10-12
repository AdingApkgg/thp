// Loopback-only TH12 delivery harness: a fixed allowlist, never the workspace.
//
// Derived from scripts/serve-sdl.mjs (the TH11 template's server). Differences:
//   - serves the TH12 page, harness and th12.dat
//   - th12.dat is read from target.json rather than a hard-coded folder name
//   - fonts and converted music are registered from their asset directories
import {createServer} from 'node:http';
import {readFile,readdir,stat} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {resolve,extname} from 'node:path';

const root=fileURLToPath(new URL('../',import.meta.url));
const target=JSON.parse(await readFile(resolve(root,'target.json'),'utf8'));
// The engine and its data are two things, and a boot of one title needs both of that title: the
// archive comes from the runtime directory that declares the title being served, so a title whose
// engine was just built is not handed another title's data.
const dataRoot=process.env.TH_DATA_ROOT??process.env.TH_RUNTIME_ROOT??root;
const dataTarget=dataRoot===root?target:JSON.parse(await readFile(resolve(dataRoot,'target.json'),'utf8'));
const wanted=String(process.env.TH_TITLE||target.game||'');
const archiveEntry=Object.entries(dataTarget.dataArchives??{}).find(([name])=>name===wanted+'.dat')
           ??Object.entries(dataTarget.dataArchives??{}).find(([,v])=>typeof v?.path==='string');
const archive=archiveEntry?.[1]?.path;
if(!archive)throw Error('target.json has no data archive for '+wanted);

async function firstExisting(candidates){
 for(const candidate of candidates){try{const info=await stat(candidate);if(info.isFile())return candidate;}catch{}}
 return null;
}

// The loader is named for the title and can be served from the build a round just made, so a
// parameterised build can be booted without renaming it by hand: TH_OUTPUT names the directory,
// target.json names the title, and the ancestor's own path stays an alias because the inherited
// shell imports it.
const harnessDir=process.env.TH_OUTPUT??'artifacts/sdl3';
// TH_TITLE serves another title's artifact from the same tree, which is what a per-title boot needs.
const game=String(process.env.TH_TITLE||target.game||'');
const harnessMjs=await firstExisting([
 resolve(root,harnessDir,game+'-harness.mjs'),
 resolve(root,harnessDir,'th11-harness.mjs'),
 resolve(root,'artifacts/sdl3',game+'-harness.mjs'),
 resolve(root,'artifacts/sdl3','th11-harness.mjs')]);
if(!harnessMjs)throw Error('no harness loader for '+game+' in '+harnessDir);

const fixed=new Map([
 ['/','sdl-runtime/th12.html'],
 ['/app/style.css','sdl-runtime/style.css'],
 ['/app/shell.mjs','sdl-runtime/shell-harness.mjs'],
 ['/app/frame-clock.mjs','sdl-runtime/frame-clock.mjs'],
 ['/app/keyboard.mjs','sdl-runtime/keyboard.mjs'],
 ['/app/directory-keyboard.mjs','sdl-runtime/directory-keyboard.mjs'],
 ['/'+game+'-harness.mjs',harnessMjs],
 ['/'+game+'-harness.wasm',harnessMjs.replace(/\.mjs$/,'.wasm')],
 // The inherited shell imports the TH11 loader path; alias it rather than fork the shell.
 ['/th11-harness.mjs',harnessMjs],
 ['/th11-harness.wasm',harnessMjs.replace(/\.mjs$/,'.wasm')],
]);
// The engine's data is the title's, so the assets are a parameter too: TH_ASSET_ROOT names the
// asset directory of the title being served, and the default is the one beside this tree.
const assetDir=resolve(process.env.TH_ASSET_ROOT??resolve(root,'assets'),'sdl-native');
// A piece the title has not converted falls back to the piece beside this tree, and which pieces
// fell back is named in the boot, because a silent fallback is how a title ends up decoding
// another title's data.
const fallbackDir=resolve(root,'assets/sdl-native');
const hasMusic=async dir=>((await stat(dir).catch(()=>null))?.isDirectory()
 &&(await readdir(dir)).some(name=>/^[a-z0-9_]+\.ogg$/.test(name)));
const hasFonts=async dir=>((await stat(dir+'/manifest.json').catch(()=>null))?.isFile());
async function pick(kind,test){
 if(await test(resolve(assetDir,kind)))return {dir:resolve(assetDir,kind),source:assetDir};
 const other=resolve(fallbackDir,kind);
 if(await test(other))return {dir:other,source:fallbackDir};
 return {dir:resolve(assetDir,kind),source:'absent'};
}
const chosenFonts=await pick('fonts',hasFonts),chosenMusic=await pick('music',hasMusic);
console.log('TH12 server: title '+game+', archive '+archive+', music from '+chosenMusic.source
 +', fonts from '+chosenFonts.source);
// The font set is a directory of .bin files, not a single file.
const fontsDir=chosenFonts.dir;
if((await stat(fontsDir).catch(()=>null))?.isDirectory()){
 for(const name of await readdir(fontsDir))if(/^[a-z0-9_]+\.bin$/.test(name))fixed.set('/fonts/'+name,fontsDir+'/'+name);
 if((await stat(fontsDir+'/manifest.json').catch(()=>null))?.isFile())fixed.set('/fonts-index.json',fontsDir+'/manifest.json');
}
// Same for the converted music: the shell fetches /music/<file> for every entry
// of /music-index.json and writes it into MEMFS for the game to decode.
const musicDir=chosenMusic.dir;
if((await stat(musicDir).catch(()=>null))?.isDirectory())
 for(const name of await readdir(musicDir))if(/^[a-z0-9_]+\.ogg$/.test(name))fixed.set('/music/'+name,musicDir+'/'+name);

const server=createServer(async(req,res)=>{
 try{
  if(!['GET','HEAD'].includes(req.method)){res.writeHead(405).end();return;}
  const path=new URL(req.url,'http://localhost').pathname;
  const types={'.html':'text/html; charset=utf-8','.mjs':'text/javascript','.css':'text/css','.wasm':'application/wasm','.json':'application/json','.bin':'application/octet-stream','.dat':'application/octet-stream'};
  let file=null;
  if(path==='/th12.dat'||path==='/th11.dat'||path==='/'+game+'.dat')file=archive;
  else if(path==='/music-index.json'){
   const bytes=Buffer.from(JSON.stringify(await readMusicIndex()));
   res.writeHead(200,{'Content-Type':'application/json','Content-Length':bytes.length,'Cache-Control':'no-store'});
   res.end(req.method==='HEAD'?undefined:bytes);return;
  }
  else if(fixed.has(path))file=resolve(root,fixed.get(path));
  if(!file){res.writeHead(404).end();return;}
  const bytes=await readFile(file);
  res.writeHead(200,{'Content-Type':types[extname(file)]||'application/octet-stream','Content-Length':bytes.length,'Cache-Control':'no-store','Cross-Origin-Opener-Policy':'same-origin','Cross-Origin-Embedder-Policy':'require-corp'});
  res.end(req.method==='HEAD'?undefined:bytes);
 }catch(e){res.writeHead(500).end('Harness resource unavailable');console.error(e.message);}
});

// The music index is derived from the encode's own verification report, so a
// track is only advertised if the converter proved it decodes to the exact
// original frame count. An empty list simply means "not converted yet".
async function readMusicIndex(){
 const manifest=await firstExisting([resolve(assetDir,'music-verification.json'),
                                   resolve(fallbackDir,'music-verification.json')]);
 if(!manifest)return [];
 try{
  // The manifest path is native, so its directory is asked for rather than cut at a slash:
  // a Windows path has none, and cutting there served an empty index once.
  const dir=resolve(manifest,'..','music');
  const names=new Set(await readdir(dir));
  const list=JSON.parse(await readFile(manifest,'utf8'));
  return list.filter(entry=>/^[a-z0-9_]+\.ogg$/.test(entry.file)&&names.has(entry.file));
 }catch{return [];}
}

const port=Number(process.env.TH12_PORT??8113);
server.listen(port,'127.0.0.1',()=>console.log(`TH12 SDL harness http://127.0.0.1:${port}`));
