// Freeze the current local TH14 verification harness, including lossless assets.
// This is not a production eagler-touhou package or a complete-game attestation.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th14/th14_web'),shared=resolve(root,'runtimes/th12/th12_web'),sourceRoot=resolve(root,'runtimes/th12');
const sha=b=>createHash('sha256').update(b).digest('hex'),json=p=>JSON.parse(readFileSync(p));
const build=json(resolve(rt,'artifacts/sdl3/build.json'));assert.equal(build.title,14);assert.equal(build.completeGame,false);
for(const group of [build.sources,build.headers]){assert(group&&Object.keys(group).length);for(const [name,hash] of Object.entries(group))assert.equal(sha(readFileSync(resolve(sourceRoot,name))),hash,'stale build '+name);}
const target=json(resolve(rt,'../target.json')),music=json(resolve(rt,'assets/sdl-native/music-verification.json')),fonts=json(resolve(rt,'assets/sdl-native/fonts/manifest.json'));
assert.equal(music.length,18);assert(music.every(r=>r.lossless===true&&r.codec==='flac'&&/^(?:th14_\d\d|th128_08)\.flac$/.test(r.file)));
const pending=[],files={};
const copy=(name,path,expected)=>{const bytes=readFileSync(path),digest=sha(bytes);if(expected)assert.equal(digest,expected,name);files[name]={bytes:bytes.length,sha256:digest};pending.push({name,path});};
copy('index.html',resolve(rt,'sdl-runtime/th14.html'));
for(const name of ['style.css','shell-harness.mjs','frame-clock.mjs','keyboard.mjs','browser-save-store.mjs'])copy('app/'+(name==='shell-harness.mjs'?'shell.mjs':name),resolve(shared,'sdl-runtime',name));
copy('th11-harness.wasm',resolve(rt,'artifacts/sdl3/th11-harness.wasm'),build.sha256);
copy('th11-harness.mjs',resolve(rt,'artifacts/sdl3/th11-harness.mjs'),build.loaderSha256);
copy('th11.dat',target.dataArchives['th14.dat'].path);assert.equal(files['th11.dat'].bytes,target.dataArchives['th14.dat'].bytes);
copy('music-index.json',resolve(rt,'assets/sdl-native/music-verification.json'));
for(const row of music){copy('music/'+row.file,resolve(rt,'assets/sdl-native/music',row.file),row.encodedSha256);assert.equal(files['music/'+row.file].bytes,row.encodedBytes);}
copy('fonts-index.json',resolve(rt,'assets/sdl-native/fonts/manifest.json'));
assert.equal(fonts.files.length,10);for(const row of fonts.files){assert(/^[a-z0-9_]+\.bin$/.test(row.file));copy('fonts/'+row.file,resolve(rt,'assets/sdl-native/fonts',row.file),row.sha256);}
const server=readFileSync(resolve(root,'tools/th14-serve-package.mjs')),serverSha256=sha(server);
// Shell, fonts and active music can change without changing the WASM bytes.
// Include the whole inventory/provenance so a later package cannot overwrite
// a frozen directory still referenced by an earlier browser proof.
const label=build.sha256.slice(0,16)+'-'+sha(JSON.stringify({build,files,serverSha256})).slice(0,12),out=resolve(rt,'artifacts/local-package',label),site=resolve(out,'site');
const write=(path,bytes)=>{mkdirSync(dirname(path),{recursive:true});if(existsSync(path))assert.equal(sha(readFileSync(path)),sha(bytes),'frozen output changed '+path);else writeFileSync(path,bytes);};
for(const {name,path} of pending){const bytes=readFileSync(path);assert.equal(sha(bytes),files[name].sha256,'resource changed while packaging '+name);write(resolve(site,name),bytes);}
let report={schema:'th14-local-harness-package/1',game:'th14',completeGame:false,nativeEquivalent:false,build,files,serverSha256,musicTracks:music.length,losslessMusic:true,musicBytes:music.reduce((n,r)=>n+r.encodedBytes,0),scope:'Frozen local verification harness with original archive/fonts and 18 lossless music resources. No dependency on external game directory after packaging. Not a production Launcher package or proof of complete-game/native equivalence.',toolSha256:sha(readFileSync(import.meta.filename))};
const manifest=resolve(out,'package.json');if(existsSync(manifest)){const previous=json(manifest);assert.deepEqual(previous.files,files);assert.deepEqual(previous.build,build);assert.equal(previous.serverSha256,serverSha256);report=previous;}else write(manifest,Buffer.from(JSON.stringify(report,null,2)+'\n'));
write(resolve(out,'serve.mjs'),server);
writeFileSync(resolve(root,'docs/porting/th14-local-package-observed-oct11.json'),JSON.stringify({passed:true,out,...report,validationToolSha256:sha(readFileSync(import.meta.filename))},null,2)+'\n');
console.log(JSON.stringify({passed:true,out,files:Object.keys(files).length,musicTracks:music.length,musicBytes:report.musicBytes,wasm:build.sha256,completeGame:false}));
