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
const allowedBuildRoot=resolve(root,'artifacts/th14/screen-camera-production-build-oct14');
const buildRelative=relative(allowedBuildRoot,buildDirectory);
assert(buildRelative&&!isAbsolute(buildRelative)&&!buildRelative.startsWith('..'), 'Only the new screen-camera build accepted');
const json=p=>JSON.parse(readFileSync(p)),build=json(resolve(buildDirectory,'build.json'));
assert.equal(build.title,14);assert.equal(build.releaseProfile,true);assert.equal(build.completeGame,false);assert.equal(build.kind,'th14-sdl3-web-release');
for(const group of [build.sources,build.headers])for(const [name,hash] of Object.entries(group))assert.equal(sha(readFileSync(resolve(root,'runtimes/th12',name))),hash,'stale release '+name);
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
const report={passed:true,completeGame:false,nativeEquivalent:false,out,buildDirectory,build,files,exports,toolSha256:sha(readFileSync(import.meta.filename)),sourceShellSha256:sha(readFileSync(resolve(shared,'sdl-runtime/shell.mjs'))),scope:'Frozen release Runtime for eagler-touhou/1 managed DATA, original TH14 save/config/replay paths,10 fonts and18 lossless FLAC tracks. Historical th11 C ABI retained; only internal archive filename bridged by a filesystem alias. No diagnostic force-stage/invulnerability/completion exports. Not yet browser-validated Host integration or complete/native-equivalent game.'};
writeFileSync(resolve(root,'docs/porting',reportName),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:true,out,files:Object.keys(files).length,resources:resources.length,bytes:build.bytes,sha256:build.sha256}));
