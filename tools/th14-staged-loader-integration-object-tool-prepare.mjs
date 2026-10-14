// Preserve the existing complete object collector; derive a separate private runner.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),original='tools/th14-continuous-late-combat-trace-check.mjs';
const old=readFileSync(resolve(root,original),'utf8'),sha=b=>createHash('sha256').update(b).digest('hex');let source=old.replaceAll('\r\n','\n');
function replace(before,after){assert(source.includes(before),before);source=source.replace(before,after);}
replace("const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web');","const root=resolve(import.meta.dirname,'..'),revision=process.env.TH14_STAGED_REVISION||'',home=resolve(root,'artifacts/th14/staged-loader-integration-oct14',revision||'.'),rt=resolve(home,revision?'source/runtimes/th12/th12_web':'private/runtimes/th12/th12_web');");
replace("const out=resolve(root,'artifacts/th14/custom-replay-reference',label||'baseline');","const out=resolve(home,'objects-playback',label||'baseline');");
replace("option('--native','artifacts/th14/native-campaign-reference-oct11.json')","option('--native','artifacts/th14/native-zps-reimua-lunatic-full-oct14/reference.compact.json')");
replace("option('--manifest','artifacts/th14/native-campaign-assets/57d84a5cbe82-cd2f2e3549c0/manifest.json')","option('--manifest','artifacts/th14/native-campaign-assets/57d84a5cbe82-0f82baec9b33/manifest.json')");
replace("option('--difficulty',1)","option('--difficulty',3)");
replace("const engine=JSON.parse(readFileSync(resolve(root,'runtimes/th13/th13_web/artifacts/cpp/engine-th14-build.json')));\nfor(const [name,hash] of Object.entries(engine.sourceHashes))","const engine=JSON.parse(readFileSync(resolve(home,'private-build.json')));\nfor(const [name,hash] of Object.entries(engine.privateSourceHashes))");
replace("objects=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14')","objects=resolve(home,'objects')");
replace("writeFileSync(fixture,fixtureSource);","fixtureSource+='\\n'+readFileSync(resolve(rt,'tests/cpp/th14-staged-loader-integration-fixture.cpp'),'utf8').split('\\n').slice(1).join('\\n');\nwriteFileSync(fixture,fixtureSource);");
replace("resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe')","resolve(root,'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe')");
replace("c.public_replay_begin(upload(replay),replay.length)","c.integration_begin(upload(replay),replay.length)");
replace("const before=c.public_replay_observations();assert.equal(c.tick(0),1);","const before=c.public_replay_observations();c.integration_clock(BigInt(index+1)*1000000000n/60n);assert.equal(c.tick(0),1);");
replace("const report={rawDetailPath,","for(const [name,hash] of Object.entries(engine.baselineSourceHashes))assert.equal(sha(readFileSync(resolve(root,'runtimes/th12/th12_web',name))),hash,'production source changed');\nconst report={privatePrototype:true,productionChanged:false,productionVerified:false,captureQueueIntegrated:false,gpuPrepared:false,clockMode:'Declared60Hz monotonic clock, not captured Native worker time',derivedCollectorSha256:'"+sha(Buffer.from(old))+"',rawDetailPath,");
replace("`docs/porting/th14-continuous-late-native-trace${label?'-'+label:''}-observed-oct13.json`","`docs/porting/th14-staged-loader-integration-object${revision?'-'+revision:''}-verified-oct14.json`");
replace("Uninterrupted warm retail capture versus unchanged production replay across all stages, including inactive loading callbacks, paired in physical callback order.","Uninterrupted immutable warm retail capture versus private integrated real-resource playback with declared60Hz test clock across all stages, including every inactive loading callback, paired in physical invocation order. Production/root source and shared objects are not modified. Headless GPU and host capture queue remain unimplemented.");
source='// Derived independent private collector; original runner and evidence stay unchanged.\n'+source;
const output='tools/th14-staged-loader-integration-objects-check.mjs';writeFileSync(resolve(root,output),source);
console.log(JSON.stringify({created:output,derivedFrom:original,originalSha256:sha(Buffer.from(old)),newSha256:sha(Buffer.from(source))}));
