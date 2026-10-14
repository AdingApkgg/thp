// Local integration harness; the user's original archive is read-only.
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {root,inside,options,handler,isMain} from './th14-local-audio-policy.mjs';
export function prepare(argv=[]){
 const settings=options(argv,['--output']),rt=resolve(root,'runtimes/th14/th14_web'),shared=resolve(root,'runtimes/th12/th12_web');
 const target=JSON.parse(readFileSync(resolve(rt,'../target.json')));assert.equal(target.game,'th14');
 const build=inside(root,resolve(rt,settings.output??process.env.TH14_OUTPUT??'artifacts/sdl3')),music=resolve(rt,'assets/sdl-native/music'),files=new Map();
 const add=(name,path)=>files.set(name,{path});
 for(const [name,path]of Object.entries({'/':resolve(rt,'sdl-runtime/th14.html'),'/app/style.css':resolve(shared,'sdl-runtime/style.css'),'/app/shell.mjs':resolve(shared,'sdl-runtime/shell-harness.mjs'),'/app/frame-clock.mjs':resolve(shared,'sdl-runtime/frame-clock.mjs'),'/app/keyboard.mjs':resolve(shared,'sdl-runtime/keyboard.mjs'),'/app/browser-save-store.mjs':resolve(shared,'sdl-runtime/browser-save-store.mjs'),'/th11-harness.mjs':resolve(build,'th11-harness.mjs'),'/th11-harness.wasm':resolve(build,'th11-harness.wasm'),'/th11.dat':target.dataArchives['th14.dat'].path,'/fonts-index.json':resolve(rt,'assets/sdl-native/fonts/manifest.json')}))add(name,path);
 for(const name of ['font0.bin','font1.bin','font2.bin','font3.bin','cp932.bin','blend4444.bin','font4.bin','font5.bin','font6.bin','font7.bin'])add('/fonts/'+name,resolve(rt,'assets/sdl-native/fonts',name));
 let index=Buffer.from('[]');try{index=readFileSync(resolve(music,'../music-verification.json'));}catch(error){if(error.code!=='ENOENT')throw error;}
 files.set('/music-index.json',{bytes:index,name:'music-index.json'});
 for(const entry of JSON.parse(index))if(/^[a-z0-9_]+\.(?:ogg|flac)$/.test(entry.file))add('/music/'+entry.file,resolve(music,entry.file));
 return {settings,files,request:handler(files,settings)};
}
if(isMain(import.meta.url)){const state=prepare(process.argv.slice(2));createServer(state.request).listen(state.settings.port,'127.0.0.1',()=>console.log(`TH14 integration http://localhost:${state.settings.port}/ (${state.settings.sound?'sound explicitly enabled':'quiet by default'})`));}
