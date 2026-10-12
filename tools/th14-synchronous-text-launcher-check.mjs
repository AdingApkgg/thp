import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),evidence={},sha=b=>createHash('sha256').update(b).digest('hex');
const track=p=>{const b=readFileSync(resolve(root,p));evidence[p]={bytes:b.length,sha256:sha(b)};return b;};
const packageReport=JSON.parse(track('docs/porting/th14-launcher-preview-prepared-oct11.json'));
const release=JSON.parse(track('runtimes/th14/th14_web/artifacts/sdl3-release/build.json'));
assert(packageReport.passed&&release.releaseProfile&&release.title===14);
assert.equal(release.sha256,'a765329908aaf597b267f2bcc888739d48d95bc089083ea8842f237fcc935c08');
for(const [p,f] of Object.entries(packageReport.files)){const b=readFileSync(resolve(packageReport.site,p));assert.equal(b.length,f.bytes,p);assert.equal(sha(b),f.sha256,p);}
const out='artifacts/th14/synchronous-text-launcher';
for(const p of ['initial-no-input-gameover.png','ordinary-retry-ranking.png'])track(out+'/'+p);
const logs=JSON.parse(track(out+'/browser-logs.json'));assert.equal(logs.length,0);
track('tools/th14-synchronous-text-launcher-check.mjs');
const report={passed:true,completeGame:false,nativeEquivalent:false,url:'http://127.0.0.1:8180/?game=th14',releaseSha256:release.sha256,verifiedPackageFiles:Object.keys(packageReport.files).length,buildId:packageReport.buildId,browserWarningsOrErrors:0,evidence,observations:{difficulty:'Normal',character:'Reimu',weapon:'A',stage:1,initialGameOverScore:11030,retryRankingScore:149931,retryRankingPower:2.77,retryRankingPointValue:10290,retryRankingGraze:35},scope:'Physical ordinary Launcher launch, title/difficulty/character/weapon selection, first-stage battle, normal collision/game-over, retry with held firing/focus, subsequent game-over score-ranking/name-input screen. No diagnostic invulnerability or natural-clear/original whole-frame equivalence claim. Earlier filename ordinary-retry-paused.png was misleading: its image is score ranking, preserved and copied to ordinary-retry-ranking.png; this report does not claim a pause check.'};
writeFileSync(resolve(root,'docs/porting/th14-synchronous-text-launcher-observed-oct12.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:true,releaseSha256:release.sha256,verifiedPackageFiles:report.verifiedPackageFiles,browserWarningsOrErrors:0}));
