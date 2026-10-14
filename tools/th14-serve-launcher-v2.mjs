import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {root,digest,inside,options,handler,isMain} from './th14-local-audio-policy.mjs';
export function prepare(argv=[]){
 const settings=options(argv,['--report']),name=settings.report??'th14-launcher-preview-prepared-screen-camera-oct15.json';assert(/^[a-z0-9-]+\.json$/.test(name));
 const proof=JSON.parse(readFileSync(resolve(root,'docs/porting',name))),site=inside(resolve(root,'runtimes/th14/th14_web/artifacts'),resolve(proof.site));assert.equal(proof.passed,true);
 const inventory={...proof.files,'files.json':{sha256:digest(readFileSync(resolve(site,'files.json')))}},files=new Map();
 for(const [name,entry]of Object.entries(inventory))files.set('/'+name,{path:inside(site,resolve(site,name)),length:entry.bytes,sha256:entry.sha256});
 assert(files.has('/index.html'));files.set('/',files.get('/index.html'));
 return {settings,files,request:handler(files,settings),reportName:name};
}
if(isMain(import.meta.url)){const state=prepare(process.argv.slice(2));createServer(state.request).listen(state.settings.port,'127.0.0.1',()=>console.log(`TH14 Launcher http://localhost:${state.settings.port}/ (${state.settings.sound?'sound explicitly enabled':'quiet by default'}; ${state.reportName})`));}
