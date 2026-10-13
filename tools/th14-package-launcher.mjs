// Local Host preview using the real shared Launcher and the TH14 release ABI.
// Original data remains in workspace artifacts; this does not publish a site.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync,existsSync} from 'node:fs';
import {resolve,dirname,relative} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),launcher=resolve(root,'runtimes/th12/th12_web/launcher'),sha=b=>createHash('sha256').update(b).digest('hex');
const option=(name,fallback)=>{const at=process.argv.indexOf(name);return at<0?fallback:process.argv[at+1];};
const runtimeReport=option('--runtime-report','th14-launcher-runtime-prepared-oct11.json'),reportName=option('--report','th14-launcher-preview-prepared-oct11.json');
for(const name of [runtimeReport,reportName])assert(/^[a-z0-9-]+\.json$/.test(name));
execFileSync(process.execPath,[resolve(root,'tools/architecture/typescript/node_modules/typescript/bin/tsc'),'-p',resolve(launcher,'tsconfig.launcher.json'),'--pretty','false'],{stdio:'inherit',windowsHide:true});
const runtime=JSON.parse(readFileSync(resolve(root,'docs/porting',runtimeReport)));assert.equal(runtime.passed,true);assert.equal(runtime.build.releaseProfile,true);
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'))),archive=readFileSync(target.dataArchives['th14.dat'].path);assert.equal(archive.length,target.dataArchives['th14.dat'].bytes);
// Assemble before choosing a directory: a shell/module-only change must not
// overwrite a previously observed deployment with the same WASM hash.
const virtualSite=resolve(root,'artifacts/th14/launcher-preview-virtual'),pendingFiles=new Map();
const write=(name,bytes)=>{assert(!name.startsWith('/')&&!name.split('/').includes('..')&&!name.includes('\\'));pendingFiles.set(name,Buffer.from(bytes));};
const copy=(name,path)=>write(name,readFileSync(path));
const walk=dir=>readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?walk(resolve(dir,e.name)):[resolve(dir,e.name)]);
const pending=['app.js'],seen=new Set(),moduleSources={};
// The shared development HTML currently has a single TH11 card. Specialize
// only this private TH14 deployment, retaining the shared Launcher behavior.
const titleText=s=>s.replaceAll('东方地灵殿','东方辉针城').replaceAll('東方地灵殿','東方辉针城').replaceAll('地灵殿','辉针城').replaceAll('Subterranean Animism','Double Dealing Character').replaceAll('Touhou 11','Touhou 14').replaceAll('支持日文原版、触控和离线游玩。','本机重建预览，支持日文原版和触控。完整原版等价尚未完成。').replaceAll('with Japanese, touch controls and offline play.','local reconstruction preview, with Japanese and touch controls. Full native equivalence is not yet established.');
function locate(name){for(const path of [resolve(launcher,'public',name),resolve(launcher,'.cache/build/browser',name),resolve(launcher,'src/browser-facades',name),resolve(launcher,name)])if(existsSync(path))return path;throw Error('Missing browser module '+name);}
while(pending.length){const name=pending.pop();if(seen.has(name))continue;assert(!name.startsWith('../')&&!name.startsWith('/'));seen.add(name);const path=locate(name),original=readFileSync(path,'utf8'),source=name.endsWith('/i18n.mjs')?titleText(original):original;assert(!/(?:from\s*|import\s*\()['"]node:/.test(source),'Node dependency in browser '+name);write(name,source);moduleSources[name]={source:path,sourceSha256:sha(Buffer.from(original)),sha256:sha(Buffer.from(source))};
 for(const match of source.matchAll(/(?:\b(?:import|export)\s+(?:[^'";]*?\s+from\s+)?|\bimport\s*\()\s*['"](\.[^'"]+)['"]/g))pending.push(relative(virtualSite,resolve(virtualSite,dirname(name),match[1])).replaceAll('\\','/'));
}
for(const path of walk(resolve(launcher,'public'))){const name=relative(resolve(launcher,'public'),path).replaceAll('\\','/');if(!/\.(?:js|mjs)$/.test(name)||name.startsWith('vendor/')||name==='native-audio.js')copy(name,path);}
let page=titleText(pendingFiles.get('index.html').toString('utf8'));
assert.equal((page.match(/data-game="th11"/g)||[]).length,1);
page=page.replace('game-th11','game-th14').replace('data-game="th11"','data-game="th14"').replace('<span class="no-label">11</span>','<span class="no-label">14</span>').replaceAll('<img class="card-art-image" src="assets/th11-card.png" alt="">','').replace('href="assets/th11-card.png" type="image/png"','href="assets/th14-icon.svg" type="image/svg+xml"');
write('index.html',page);
write('assets/th14-icon.svg','<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="#10100f"/><text x="32" y="44" text-anchor="middle" font-family="sans-serif" font-size="36" fill="#eeccdd">14</text></svg>');
write('styles.css',pendingFiles.get('styles.css').toString('utf8')+'\n.game-th14 .card-art{background:radial-gradient(ellipse at 70% 25%,#754775,transparent 65%),linear-gradient(135deg,#23182d,#452132)}\n');
const siteManifest=JSON.parse(pendingFiles.get('site.webmanifest'));siteManifest.name='东方辉针城网页版（重建预览）';siteManifest.short_name='辉针城';siteManifest.description='本机源码重建预览，完整原版等价尚未完成。';siteManifest.icons=[{src:'assets/th14-icon.svg',sizes:'any',type:'image/svg+xml'}];write('site.webmanifest',JSON.stringify(siteManifest,null,2)+'\n');
for(const [name,row] of Object.entries(runtime.files)){const path=resolve(runtime.out,name),bytes=readFileSync(path);assert.equal(sha(bytes),row.sha256);assert.equal(bytes.length,row.bytes);write('runtime/th14/'+name,bytes);}
copy('runtime/th14/runtime-files.json',resolve(runtime.out,'runtime-files.json'));
write('packages/th14/th14.data',archive);
const dataHash=sha(archive),layout='sha256-'+sha(Buffer.from(JSON.stringify({files:[{filename:'/th14.data'}]}))),revision='th14-1.00b-preview-'+dataHash.slice(0,12);
const json=(name,value)=>write(name,JSON.stringify(value,null,2)+'\n');
json('packages/th14/package.json',{schema:'eagler-touhou/package/1',game:'th14',revision,files:{'game-data':{source:'th14.data',target:'/th14.data',bytes:archive.length,revision:'sha256-'+dataHash}},base:{files:['game-data']},components:{},runtimeRequirement:{protocol:'eagler-touhou/1',target:'th14',dataFile:'game-data',dataLayout:layout}});
json('release-catalog.json',{schema:'eagler-touhou/release-catalog/1',games:{th14:{revision,descriptor:'./packages/th14/package.json'}}});
json('host-manifest.json',{schema:'eagler-touhou/host-manifest/1',protocol:'eagler-touhou/1',profile:'th14-sdl3-preview',shared:{resourceMode:'hosted',vanillaFont:'',unicodeFont:''},games:{th14:{runtime:'./runtime/th14/th14.html',gameData:{path:'th14.data',bytes:archive.length,sha256:dataHash,version:'sha256-'+dataHash,layout},music:{midi:{files:[]}},languageOptions:[{id:'ja',title:'日本語（原版）',pack:null}],features:{thprac:false,focusHitbox:false}}}});
json('manifest.json',{game:'th14',version:'1.00b-reconstruction-preview',completeGame:false,nativeEquivalent:false,execution:{kind:runtime.build.kind,bytes:runtime.build.bytes,sha256:runtime.build.sha256,loaderSha256:runtime.build.loaderSha256}});
copy('LICENSE-launcher.txt',resolve(launcher,'LICENSE'));
write('THIRD-PARTY-NOTICES.txt','Original game/assets: Team Shanghai Alice / ZUN. Private local reference assets.\nLauncher: YomotsuHisami/eagler-touhou, GPL-3.0-or-later.\nSDL3: zlib. Emscripten: MIT/UIUC. miniaudio: public domain/MIT.\n');
write('CHANGELOG.txt','辉针城 WEB：本机源码重建预览，完整原版等价尚未完成。\n');
const precache=[...pendingFiles.keys()].filter(n=>n!=='files.json'&&n!=='app-shell-sw.js'&&!n.startsWith('packages/'));
const entries=[{url:'./',revision:sha(pendingFiles.get('index.html'))},...precache.sort().map(n=>({url:n,revision:sha(pendingFiles.get(n))}))],buildId=sha(Buffer.from(JSON.stringify(entries))).slice(0,20);
if(existsSync(resolve(launcher,'src/app-shell-sw.js')))write('app-shell-sw.js',readFileSync(resolve(launcher,'src/app-shell-sw.js'),'utf8').replaceAll('__APP_SHELL_BUILD_ID__',buildId).replace('self.__WB_MANIFEST',JSON.stringify(entries)));
const files=Object.fromEntries([...pendingFiles.keys()].sort().map(name=>[name,{bytes:pendingFiles.get(name).length,sha256:sha(pendingFiles.get(name))}]));json('files.json',Object.fromEntries(Object.entries(files).map(([name,r])=>[name,r.sha256])));
const toolSha256=sha(readFileSync(import.meta.filename)),label=runtime.build.sha256.slice(0,16)+'-'+sha(Buffer.from(JSON.stringify({files,toolSha256}))).slice(0,12),out=resolve(root,'runtimes/th14/th14_web/artifacts/launcher-preview',label),site=resolve(out,'site');
for(const [name,bytes] of pendingFiles){const path=resolve(site,name);mkdirSync(dirname(path),{recursive:true});if(existsSync(path))assert.equal(sha(readFileSync(path)),sha(bytes),'immutable Launcher '+name);else writeFileSync(path,bytes);}
const report={passed:true,completeGame:false,nativeEquivalent:false,out,site,files,moduleSources,buildId,revision,runtimeManifestSha256:sha(readFileSync(resolve(root,'docs/porting',runtimeReport))),toolSha256,scope:'Local preview of the real shared Launcher plus TH14 release-profile Runtime, original managed DATA, persistent TH14 score/config/replay paths and original lossless/font resources. Built module graph rejects Node dependencies. Not yet a browser/offline verification or a published complete game.'};
const reportBytes=Buffer.from(JSON.stringify(report,null,2)+'\n'),reportPath=resolve(out,'release.json');if(existsSync(reportPath))assert.equal(sha(readFileSync(reportPath)),sha(reportBytes),'immutable Launcher proof');else writeFileSync(reportPath,reportBytes);writeFileSync(resolve(root,'docs/porting',reportName),reportBytes);console.log(JSON.stringify({passed:true,site,files:Object.keys(files).length,browserModules:seen.size,buildId}));
