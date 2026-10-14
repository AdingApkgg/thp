import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFileSync,realpathSync} from 'node:fs';
import {resolve} from 'node:path';
import {root,inside,options,handler,isMain} from './th14-local-audio-policy.mjs';
export function prepare(argv=[]){
 const settings=options(argv,['--package-root']);assert(settings['package-root'],'--package-root is required');
 const directory=inside(realpathSync(root),realpathSync(resolve(root,settings['package-root']))),manifest=JSON.parse(readFileSync(resolve(directory,'package.json')));
 assert.equal(manifest.schema,'th14-local-harness-package/1');assert.equal(manifest.game,'th14');const site=inside(directory,resolve(directory,'site')),files=new Map();
 for(const [name,entry]of Object.entries(manifest.files))files.set('/'+name,{path:inside(site,resolve(site,name)),length:entry.bytes,sha256:entry.sha256});
 assert(files.has('/index.html'));files.set('/',files.get('/index.html'));
 return {settings,files,request:handler(files,settings),directory};
}
if(isMain(import.meta.url)){const state=prepare(process.argv.slice(2));createServer(state.request).listen(state.settings.port,'127.0.0.1',()=>console.log(`TH14 package http://localhost:${state.settings.port}/ (${state.settings.sound?'sound explicitly enabled':'quiet by default'})`));}
