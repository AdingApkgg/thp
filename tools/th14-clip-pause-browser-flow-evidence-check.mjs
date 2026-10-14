// Observe current release playback of the ordinary recording saved previously.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),sha=b=>createHash('sha256').update(b).digest('hex'),bindings={};
const read=name=>{const b=readFileSync(resolve(root,name));bindings[name]={bytes:b.length,sha256:sha(b)};return b;};
const load=name=>JSON.parse(read(name));
const build=load('runtimes/th14/th14_web/artifacts/sdl3-release/build.json');
assert.equal(build.title,14);assert(build.releaseProfile&&!build.completeGame);
for(const [name,digest] of Object.entries({...build.headers,...build.sources}))assert.equal(sha(read('runtimes/th12/'+name)),digest,name);
const wasm=read('runtimes/th14/th14_web/artifacts/sdl3-release/th11.wasm');assert.equal(sha(wasm),build.sha256);
assert(!WebAssembly.Module.exports(new WebAssembly.Module(wasm)).some(row=>/^th11_(?:probe_|audio_probe|audio_samples|tick$)/.test(row.name)));
const rp='docs/porting/th14-launcher-runtime-prepared-clip-pause-oct14.json',runtime=load(rp);
assert.equal(runtime.build.sha256,build.sha256);assert.deepEqual(runtime.build.sources,build.sources);assert.deepEqual(runtime.build.headers,build.headers);
const preview=load('docs/porting/th14-launcher-preview-prepared-clip-pause-oct14.json');
assert(preview.passed&&!preview.nativeEquivalent);assert.equal(preview.runtimeManifestSha256,bindings[rp].sha256);
for(const [name,row] of Object.entries(preview.files)){const b=readFileSync(resolve(preview.site,name));assert.equal(b.length,row.bytes);assert.equal(sha(b),row.sha256,name);}
const base='artifacts/th14/browser-clip-pause-oct14/',screenshots=['replay-list-after-update.jpg','replay-playing.jpg','replay-returned.jpg'];
for(const name of screenshots)assert.equal(read(base+name).subarray(0,3).toString('hex'),'ffd8ff');
const observation=load(base+'observation.json');
const allLogs=load(base+'console.json'),logs=allLogs.filter(row=>row.level==='warn'||row.level==='error');assert.equal(logs.length,2);assert(logs.every(row=>row.level==='warn'&&row.message.startsWith('App Shell update check unavailable')));
assert.deepEqual(logs.map(row=>row.timestamp),['2026-10-14T04:07:44.683Z','2026-10-14T04:33:06.632Z']);
const sinceAt=process.argv.indexOf('--since');assert(sinceAt>=0,'--since required for the observed current launch');const since=process.argv[sinceAt+1];assert(/^2026-10-14T/.test(since));const currentLogs=allLogs.filter(row=>row.timestamp>=since);
assert.equal(since,observation.currentLaunchSince);
const startup=currentLogs.find(row=>row.message.startsWith('[loading14] ascii script17 started;'));
assert(startup&&Date.parse(startup.timestamp)-Date.parse(since)>=0&&Date.parse(startup.timestamp)-Date.parse(since)<15000);
assert(currentLogs.some(row=>row.message==='[replay] selected: record stage 1, character 0 subtype 0 difficulty 1, 631 bytes'));
assert(currentLogs.some(row=>row.message==='[loading14] resource uploads complete; interrupt1 delivered'));
assert(!currentLogs.some(row=>row.level==='warn'||row.level==='error'));
const shell=load('docs/porting/th14-app-shell-precache-clip-pause-verified-oct14.json');assert(shell.appShellPolicySatisfied);
const codec=load('docs/porting/th14-browser-saved-replay-native-codec-oct14.json'),row=codec.rows[0];
assert(codec.passed&&row.actualNativeCodecVerified&&row.stages[0].frames===468);
assert.equal(sha(read('artifacts/th14/browser-focused-growth-oct14/browser-normal-recording.rpy')),row.sha256);
assert.equal(sha(read('tools/th14-browser-saved-replay-native-codec-check.py')),codec.toolSha256);
const report={observedBrowserFlowVerified:true,completeGame:false,nativeEquivalent:false,url:'http://localhost:8207/?game=th14',
 build,filesVerified:Object.keys(preview.files).length,replayFrames:468,replaySha256:row.sha256,recordedUnderPreviousBuild:true,
 currentLaunchSince:since,observation,
 screenshots:screenshots.map(name=>base+name),consoleWarnings:2,consoleErrors:0,consoleEntries:logs,currentConsoleEntries:currentLogs,currentConsoleWarnings:0,currentConsoleErrors:0,appShellPrecacheReportSha256:bindings['docs/porting/th14-app-shell-precache-clip-pause-verified-oct14.json'].sha256,bindings,toolSha256:sha(readFileSync(import.meta.filename)),
 observations:['Reloaded the same origin after changing the owned preview server to the new frozen clip-composition and pause-dialogue release; the installed private DATA remained.',
 'Ordinary title -> Replay shows persisted slot01 A ReimuA Normal Stage1.',
 'Ordinary slot01 -> Stage1 plays the468 previously recorded frames without further gameplay input; current source builds the TH14 clip-composition and pause-dialogue correction; screenshots do not certify pixel equality.',
 'Playback naturally returns to the game Replay list.',
 'Both historical Launcher Service Worker update-check warnings are retained. Current launch and playback have no additional warnings or captured errors; offline readiness is not claimed.'],
 scope:'CUA-observed current release menu selection, persistence across build update, playback and natural return of an ordinary468-frame recording previously saved and independently decoded with original4028e0/465840. This does not claim the recording was saved anew under this source, original executable playback, every intermediate action mechanically proven by screenshots, full browser clear, score persistence, offline readiness, pixels/audio or whole-game1:1. All146 sources/145 headers and127 frozen files are bound; data/replay/screenshots remain private.'};
writeFileSync(resolve(root,'docs/porting/th14-clip-pause-browser-flow-verified-oct14.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({observedBrowserFlowVerified:true,sha256:build.sha256,replayFrames:468,consoleWarnings:2,consoleErrors:0}));
