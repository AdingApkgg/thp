// Bind observed ordinary browser flow to the frozen current release inventory.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),sha=b=>createHash('sha256').update(b).digest('hex'),evidence={};
const read=path=>{const bytes=readFileSync(resolve(root,path));evidence[path]={bytes:bytes.length,sha256:sha(bytes)};return bytes;};
const build=JSON.parse(read('runtimes/th14/th14_web/artifacts/sdl3-release/build.json'));
assert.equal(build.title,14);assert(build.releaseProfile&&!build.completeGame);
for(const [name,digest] of Object.entries({...build.headers,...build.sources}))assert.equal(sha(read('runtimes/th12/'+name)),digest,name);
const wasm=read('runtimes/th14/th14_web/artifacts/sdl3-release/th11.wasm');assert.equal(sha(wasm),build.sha256);
const exports=WebAssembly.Module.exports(new WebAssembly.Module(wasm)).map(row=>row.name);
assert(!exports.some(name=>/^th11_(?:probe_|audio_probe|audio_samples|tick$)/.test(name)));
const runtime=JSON.parse(read('docs/porting/th14-launcher-runtime-prepared-shared-angle-oct14.json'));
assert.equal(runtime.build.sha256,build.sha256);assert.deepEqual(runtime.build.sources,build.sources);assert.deepEqual(runtime.build.headers,build.headers);
const preview=JSON.parse(read('docs/porting/th14-launcher-preview-prepared-shared-angle-oct14.json'));
assert(preview.passed&&!preview.completeGame&&!preview.nativeEquivalent);
assert.equal(preview.runtimeManifestSha256,evidence['docs/porting/th14-launcher-runtime-prepared-shared-angle-oct14.json'].sha256);
for(const [name,row] of Object.entries(preview.files)){const bytes=readFileSync(resolve(preview.site,name));assert.equal(bytes.length,row.bytes);assert.equal(sha(bytes),row.sha256,name);}
const screenshot='artifacts/th14/browser-shared-angle-oct14/normal-reimua-paused.jpg';assert.equal(read(screenshot).subarray(0,3).toString('hex'),'ffd8ff');
assert.deepEqual(JSON.parse(read('artifacts/th14/browser-shared-angle-oct14/console.json')),[]);
const report={observedBrowserFlowVerified:true,completeGame:false,nativeEquivalent:false,url:'http://localhost:8205/?game=th14',
 build,filesVerified:Object.keys(preview.files).length,screenshotPath:screenshot,evidence,
 observations:['Original attract demo played and ordinary Escape returned to title.','Ordinary Game Start -> Normal -> Reimu ->妖器使用 A -> stage1.','Ordinary Shift+Z shooting and Escape pause; ordinary stage1 weapon effects visible.','Zero captured browser console warnings/errors. No game-state injection or diagnostic exports used.'],
 toolSha256:sha(readFileSync(import.meta.filename)),scope:'CUA-observed ordinary menu, short gameplay and pause on the frozen current release on a fresh local origin, bound to all146 sources/144 headers,127 local files and screenshot. It does not certify full browser clear, all menus/ending, original pixels/audio, score IndexedDB reload or whole-game1:1. Original data remains private/local.'};
writeFileSync(resolve(root,'docs/porting/th14-shared-angle-browser-flow-verified-oct14.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({observedBrowserFlowVerified:true,sha256:build.sha256,filesVerified:report.filesVerified}));
