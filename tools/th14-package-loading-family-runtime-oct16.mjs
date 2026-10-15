// TH14 loading-family release; preserves every earlier runtime and the tested save delta helper.
// Derived from frozen earlier packager SHA256 54b30eb6ad49c0cdcf766e046338bb9368cfeeaaa16ce435788f6e36d3de5d80.
// Freeze the real release ABI for the shared Launcher; no diagnostic exports.
// Private original fonts/music are local resources, DATA arrives from the Host.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve,dirname,relative,isAbsolute} from 'node:path';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),shared=resolve(root,'runtimes/th12/th12_web'),rt=resolve(root,'runtimes/th14/th14_web'),sha=b=>createHash('sha256').update(b).digest('hex');
const at=process.argv.indexOf('--report'),reportName=at<0?'th14-launcher-runtime-prepared-oct11.json':process.argv[at+1];assert(/^[a-z0-9-]+\.json$/.test(reportName));
assert(at>=0&&!existsSync(resolve(root,'docs/porting',reportName)), 'Explicit unused report name required');
const buildAt=process.argv.indexOf('--build-directory');
assert(buildAt>=0&&process.argv[buildAt+1], 'Explicit new workspace build directory required');
const buildDirectory=resolve(root,process.argv[buildAt+1]);
assert.equal(buildDirectory,resolve(root,'artifacts/th14/loading-anm-sdl-build-oct16'),'Only the independently built loading-family release accepted');
const json=p=>JSON.parse(readFileSync(p)),rawBuild=json(resolve(buildDirectory,'build.json'));
const build={...rawBuild,kind:'th14-sdl3-web-release',sources:rawBuild.sourceHashes,headers:rawBuild.headerHashes,sha256:rawBuild.wasmSha256,bytes:rawBuild.wasmBytes};
assert.equal(build.title,14);assert.equal(build.releaseProfile,true);assert.equal(build.completeGame,false);assert.equal(build.kind,'th14-sdl3-web-release');
assert(process.argv.includes('--frozen-release-snapshot'),'Explicit frozen release snapshot required');
assert.equal(build.sha256,'f798639ddabdc0be3b278dbf56fed2b43e4a27b78b964f8f9cddff5d3b4fb4ec');
for(const group of [build.sources,build.headers])for(const [name,hash] of Object.entries(group))assert.equal(sha(readFileSync(resolve(buildDirectory,'source',name))),hash,'stale frozen release '+name);
for(const [name,hash] of Object.entries(build.objectHashes))assert.equal(sha(readFileSync(resolve(buildDirectory,name))),hash,'stale frozen object '+name);
const wasm=readFileSync(resolve(buildDirectory,'th11.wasm')),loader=readFileSync(resolve(buildDirectory,'th11.mjs'));
assert.equal(sha(wasm),build.sha256);assert.equal(sha(loader),build.loaderSha256);
const exports=WebAssembly.Module.exports(new WebAssembly.Module(wasm));assert(!exports.some(e=>/^th11_(?:probe_|audio_probe|audio_samples|tick$)/.test(e.name)));
const resources=[],pending=new Map(),put=(name,bytes)=>{assert(!pending.has(name));pending.set(name,Buffer.from(bytes));},copy=(name,path)=>put(name,readFileSync(path));
let shell=readFileSync(resolve(shared,'sdl-runtime/shell.mjs'),'utf8');
const replace=(old,value)=>{assert(shell.includes(old),'missing shell anchor '+old);shell=shell.replaceAll(old,value);};
replace("game='th11'","game='th14'");replace('th11-sdl.mjs','th14-sdl.mjs');replace('th11-sdl.wasm','th14-sdl.wasm');
replace('/savesth11','/savesth14');replace('scoreth11','scoreth14');replace('th11\\.cfg','th14\\.cfg');replace("'th11.cfg'","'th14.cfg'");replace('th11_(?:','th14_(?:');replace('/thcrap/th11/','/thcrap/th14/');
replace('TH11','TH14');replace('地灵殿','辉针城');
replace("/*TH14_BUILD_INFO*/{version:'development-incomplete',completeGame:false}",`/*TH14_BUILD_INFO*/${JSON.stringify({version:'1.00b-reconstruction-preview',completeGame:false,nativeEquivalent:false,sha256:build.sha256})}`);
// The inherited C ABI still opens /th11.dat internally. Keep title identity,
// managed DATA and save paths TH14; bridge only this private filesystem name.
replace('await mountData();',"await mountData();\n Module.FS.symlink('/th14.dat','/th11.dat');");
assert(!shell.includes('/savesth11')&&!shell.includes('scoreth11')&&!shell.includes('th11\\.cfg'));
// Keep the canonical shared shell and historical runtime immutable. These
// changes apply only to the generated TH14 shell, with the same release WASM.
const saveDeltaSource=readFileSync(resolve(rt,'browser-save-delta.mjs'),'utf8');
const oldSync="const sync=(populate=false)=>{const current=storageSync.then(()=>new Promise((r,j)=>Module.FS.syncfs(populate,e=>e?j(e):r())));storageSync=current.catch(()=>{});return current;};";
assert(shell.includes(oldSync));
shell=shell.replace(oldSync,"let th14SaveDelta;\nconst sync=(populate=false)=>{const current=storageSync.then(()=>populate?new Promise((r,j)=>Module.FS.syncfs(true,e=>e?j(e):r())):th14SaveDelta.flush());storageSync=current.catch(()=>{});return current;};");
const mount="Module.FS.mkdirTree('/savesth14');Module.FS.mount(Module.IDBFS,{},'/savesth14');await sync(true);";
assert(shell.includes(mount));shell=shell.replace(mount,mount+"\n th14SaveDelta=th14IdbfsDeltaAdapter(Module);await th14SaveDelta.loaded();");
// Idle management commands may refresh from persistent storage. Running games
// keep their local filesystem and ordinary frame timing unchanged.
const list="case 'list':{const files=[];";assert(shell.includes(list));
shell=shell.replace(list,"case 'list':{if(!launched){await sync(true);th14SaveDelta=th14IdbfsDeltaAdapter(Module);await th14SaveDelta.loaded();Module.FS.mkdirTree('/savesth14/replay');}const files=[];");
const writeCommand="Module.FS.writeFile('/savesth14/'+target,bytes);await sync(false);return {};";assert(shell.includes(writeCommand));
shell=shell.replace(writeCommand,"const destination='/savesth14/'+target;let previous;try{previous={bytes:Module.FS.readFile(destination),stat:Module.FS.stat(destination)};}catch(e){if(e.errno!==44)throw e;}Module.FS.writeFile(destination,bytes);try{await sync(false);}catch(e){if(previous){Module.FS.writeFile(destination,previous.bytes);Module.FS.chmod(destination,previous.stat.mode);Module.FS.utime(destination,previous.stat.atime,previous.stat.mtime);}else Module.FS.unlink(destination);throw e;}return {};");
const remove="case 'remove':{if(launched)throw Error('请先退出游戏');Module.FS.unlink('/savesth14/'+path(m.path));await sync(false);return {};}";assert(shell.includes(remove));
shell=shell.replace(remove,"case 'remove':{if(launched)throw Error('请先退出游戏');const destination='/savesth14/'+path(m.path),bytes=Module.FS.readFile(destination),stat=Module.FS.stat(destination);Module.FS.unlink(destination);try{await sync(false);}catch(e){Module.FS.writeFile(destination,bytes);Module.FS.chmod(destination,stat.mode);Module.FS.utime(destination,stat.atime,stat.mtime);throw e;}return {};}");
shell+='\n'+saveDeltaSource.replace(/^export function /gm,'function ');
put('shell.mjs',shell);
let html=readFileSync(resolve(shared,'sdl-runtime/managed.html'),'utf8').replaceAll('地灵殿','辉针城');html=html.replace('<head>','<head><meta name="eagler-data-provider" content="retail-memory">');put('th14.html',html);
for(const name of ['managed.css','keyboard.mjs','directory-keyboard.mjs','eagler-host.mjs','runtime-epoch.mjs'])copy(name,resolve(shared,'sdl-runtime',name));
let motion=readFileSync(resolve(root,'runtimes/th12/portable/browser/motion-replay.mjs'),'utf8').replaceAll('TH11','TH14').replaceAll('t11r','t13r').replace('0x72313174','0x72333174').replace('74 31 31 72','74 31 33 72');put('motion-replay.mjs',motion);
put('th14-sdl.wasm',wasm);put('th14-sdl.mjs',loader);
const fonts=json(resolve(rt,'assets/sdl-native/fonts/manifest.json')),music=json(resolve(rt,'assets/sdl-native/music-verification.json'));assert.equal(fonts.files.length,10);assert.equal(music.length,18);
for(const row of fonts.files){const bytes=readFileSync(resolve(rt,'assets/sdl-native/fonts',row.file));assert.equal(sha(bytes),row.sha256);put('fonts/'+row.file,bytes);resources.push({path:'/fonts/'+row.file,url:'./fonts/'+row.file,bytes:bytes.length,sha256:sha(bytes)});}
for(const row of music){assert.equal(row.codec,'flac');assert.equal(row.lossless,true);const bytes=readFileSync(resolve(rt,'assets/sdl-native/music',row.file));assert.equal(sha(bytes),row.encodedSha256);assert.equal(bytes.length,row.encodedBytes);put('music/'+row.file,bytes);resources.push({path:'/music/'+row.file,url:'./music/'+row.file,bytes:bytes.length,sha256:sha(bytes)});}
put('resources.json',JSON.stringify({schema:'eagler-sdl-resources/1',game:'th14',resources},null,2)+'\n');
put('manifest.json',JSON.stringify({game:'th14',protocol:'eagler-touhou/1',adapter:'sdl3-eagler',profile:'production',version:'1.00b-reconstruction-preview',completeGame:false,nativeEquivalent:false,features:{thprac:false,languages:false,focusHitbox:false},music:['midi','none'],touchReplay:true,execution:{kind:build.kind,sha256:build.sha256,loaderSha256:build.loaderSha256}},null,2)+'\n');
const files=Object.fromEntries([...pending].map(([name,bytes])=>[name,{bytes:bytes.length,sha256:sha(bytes)}]));
const label=build.sha256.slice(0,16)+'-'+sha(JSON.stringify(files)).slice(0,12),out=resolve(rt,'artifacts/launcher-runtime',label);
const write=(name,bytes)=>{const path=resolve(out,name);mkdirSync(dirname(path),{recursive:true});if(existsSync(path))assert.equal(sha(readFileSync(path)),sha(bytes),'immutable runtime '+name);else writeFileSync(path,bytes);};
for(const [name,bytes] of pending)write(name,bytes);
write('runtime-files.json',Buffer.from(JSON.stringify({schema:'eagler-touhou/runtime-directory/1',game:'th14',files},null,2)+'\n'));
const report={passed:true,completeGame:false,nativeEquivalent:false,out,buildDirectory,build,files,exports,toolSha256:sha(readFileSync(import.meta.filename)),sourceShellSha256:sha(readFileSync(resolve(shared,'sdl-runtime/shell.mjs'))),sourceSaveDeltaSha256:sha(Buffer.from(saveDeltaSource)),sameProductionWasm:false,baseProductionWasmSha256:'7e42a509065676ece981f2e8e5e7ce9a86d2960d02149398b1c0c0316c15f088',sourceSnapshotBound:true,currentWorkspaceSourcesVerified:false,scope:'TH14 retained-stage loading family restored in frozen new SDL module; previously verified file delta persistence retained. Frozen release Runtime for eagler-touhou/1 managed DATA, original TH14 save/config/replay paths,10 fonts and18 lossless FLAC tracks. Historical th11 C ABI retained; only internal archive filename bridged by a filesystem alias. No diagnostic force-stage/invulnerability/completion exports. Browser validation is recorded separately; not a complete/native-equivalent game.'};
writeFileSync(resolve(root,'docs/porting',reportName),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:true,out,files:Object.keys(files).length,resources:resources.length,bytes:build.bytes,sha256:build.sha256}));
