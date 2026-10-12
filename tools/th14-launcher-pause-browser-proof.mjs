import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve,relative} from 'node:path';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),read=n=>readFileSync(resolve(root,n)),sha=b=>createHash('sha256').update(b).digest('hex');
// Pin the observed deployment, never relabel screenshots using a mutable prepared pointer.
const preparedPath='runtimes/th14/th14_web/artifacts/launcher-preview/8e66fa41b0b62a74/release.json',prepared=JSON.parse(read(preparedPath));
assert.equal(prepared.passed,true);
for(const [name,row] of Object.entries(prepared.files)){const b=readFileSync(resolve(prepared.site,name));assert.equal(b.length,row.bytes);assert.equal(sha(b),row.sha256);}
const names=['pause-confirm-fixed','pause-manual-menu','pause-manual-page','pause-manual-return','pause-restart-confirm','pause-restarted'].map(n=>'browser-launcher-'+n+'-oct11.png').concat(['browser-launcher-pause-fixed-logs-oct11.json','browser-launcher-pause-fixed-dom-oct11.txt']);
const evidence=Object.fromEntries(names.map(n=>{const path='artifacts/th14/'+n,b=read(path);return [path,{bytes:b.length,sha256:sha(b)}];}));
assert.deepEqual(JSON.parse(read('artifacts/th14/browser-launcher-pause-fixed-logs-oct11.json')),[]);
const nativePath='docs/porting/th14-pause-controls-verified-oct11.json',native=JSON.parse(read(nativePath));assert.equal(native.passed,true);
const report={passed:true,completeGame:false,nativeEquivalent:false,url:'http://127.0.0.1:8135/?game=th14',buildId:prepared.buildId,preparedPath,preparedSha256:sha(read(preparedPath)),runtimeManifestSha256:prepared.runtimeManifestSha256,nativeControls:{path:nativePath,sha256:sha(read(nativePath))},evidence,observed:['Normal Reimu A ordinary stage1 pause with all five choices','Save Replay confirmation now visibly draws Yes and No; X with No selected returns to the same pause choice','Manual enters the seven-topic original resource menu, opens first text page and two X inputs return to pause with Manual selected','Restart opens confirmation; Up selects Yes; Z restarts actual stage1, followed by pause showing score0, lives2, bombs3 and power1.00','Current error/warn logs empty'],limits:['Only the first manual body page is observed in this release; prior title-manual seven-page observations are separate historical evidence','No new replay file was saved during this pause verification; earlier Launcher persistence/export/import report remains pinned to its earlier release','Native control fixture isolates ANM and audio services; browser observation is not GPU pixel or audible output equality','No full ordinary campaign, byte-exact config persistence, offline verification or whole-game native equivalence claim']};
writeFileSync(resolve(root,'docs/porting/th14-launcher-pause-browser-observed-oct11.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:true,buildId:prepared.buildId,evidenceFiles:names.length}));
