// Run the existing ordinary ending/results/storage flow with a fresh label,
// current objects, controlled monotonic clock and explicit headless retirement.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web');
const label=process.argv[2];assert(/^[a-z0-9-]{1,64}$/.test(label));
const base=resolve(root,'artifacts/th14/natural-input',label),sha=bytes=>createHash('sha256').update(bytes).digest('hex');
assert(!existsSync(base),'Choose a new immutable result label');
const old=resolve(root,'artifacts/th14/natural-input/normal-sakuyaa-template-layer-oct14');
const inputBytes=readFileSync(resolve(old,'held-keys.u32')),inputReportBytes=readFileSync(resolve(old,'report.json'));
const inputReport=JSON.parse(inputReportBytes);
assert.equal(sha(inputBytes),inputReport.inputsSha256);assert.equal(inputBytes.length,inputReport.frames*4);
assert(inputReport.naturalClear&&inputReport.selection===4&&inputReport.difficulty===1);
const engineBytes=readFileSync(resolve(root,'runtimes/th13/th13_web/artifacts/cpp/engine-th14-build.json')),engine=JSON.parse(engineBytes);
for(const [path,hash]of Object.entries(engine.sourceHashes))assert.equal(sha(readFileSync(resolve(rt,path))),hash,path);
assert(readFileSync(resolve(rt,'cpp/game/GameSession.hpp'),'utf8').includes('stage_load_clock'));
mkdirSync(base,{recursive:true});writeFileSync(resolve(base,'held-keys.u32'),inputBytes);writeFileSync(resolve(base,'report.json'),inputReportBytes);
writeFileSync(resolve(base,'engine-build.json'),engineBytes);
const fixture=resolve(base,'storage-clock-fixture.cpp');
writeFileSync(fixture,`#include "${resolve(rt,'tests/cpp/th14-normal-natural-storage-fixture.cpp').replaceAll('\\','/')}"\n`+
  'static u64 storage_clock_ns=0;static u32 storage_clock_frames=0;\n'+
  'API(storage_clock_tick) u32 storage_clock_tick(u32 held){storage_clock_ns=u64(++storage_clock_frames)*1000000000ull/60;session.stage_load_clock=[](){return storage_clock_ns;};return tick(held);}\n'+
  'API(storage_clock_draw) u32 storage_clock_draw(){const auto result=draw();if(result)session.animations.retire_deferred_captures_without_target();return result;}\n');
const driverPath=resolve(root,'tools/th14-normal-natural-storage-check.mjs'),driverBytes=readFileSync(driverPath);
let driver=driverBytes.toString('utf8');
function replaceOnce(before,after){assert.equal(driver.split(before).length,2,before);driver=driver.replace(before,after);}
replaceOnce("const root=resolve(import.meta.dirname,'..')",'const root='+JSON.stringify(root));
replaceOnce("fixture='tests/cpp/th14-normal-natural-storage-fixture.cpp'",'fixture='+JSON.stringify(fixture));
replaceOnce("...readdirSync(objects).filter(n=>n.endsWith('.o')).map(n=>resolve(objects,n))",
  "...engine.sources.map(n=>resolve(objects,n.replaceAll('/','_')+'.o'))");
assert(driver.includes('c.tick(')&&driver.includes('c.draw('));
driver=driver.replaceAll('c.tick(','c.storage_clock_tick(').replaceAll('c.draw(','c.storage_clock_draw(');
replaceOnce("+'-observed-oct13.json'","+'-observed-oct14.json'");
const generated=resolve(base,'storage-clock-driver.mjs');writeFileSync(generated,driver);
const preparation={prepared:true,executed:false,completeGame:false,nativeEquivalent:false,
  originalDriverSha256:sha(driverBytes),generatedDriverSha256:sha(Buffer.from(driver)),generatedFixtureSha256:sha(readFileSync(fixture)),
  archivedInputSha256:sha(inputBytes),archivedInputReportSha256:sha(inputReportBytes),engineBuildSha256:sha(engineBytes),
  sourceHashes:engine.sourceHashes,toolSha256:sha(readFileSync(import.meta.filename)),
  clockMode:'Declared60Hz integer ns advanced for each ordinary tick, including ending/results; no retail timing claim',
  captureRetirement:'Explicit no-target consumer after successful headless draw',
  scope:'Archival keys are immutable inputs only. Existing storage flow driver is copied and bound, never edited; new fixture only injects monotonic clock and no-target postDraw handling. Fresh current object list excludes stale cache members.'};
writeFileSync(resolve(base,'staged-driver-prepared.json'),JSON.stringify(preparation,null,2)+'\n');
try{
  execFileSync(process.execPath,[generated,'--label',label],{cwd:root,windowsHide:true,stdio:'inherit'});
}catch(error){
  writeFileSync(resolve(base,'execution-failed.json'),JSON.stringify({failed:true,error:String(error),preparedReportSha256:sha(readFileSync(resolve(base,'staged-driver-prepared.json')))},null,2)+'\n');
  throw error;
}
