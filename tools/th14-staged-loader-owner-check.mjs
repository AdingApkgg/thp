// Controlled original retirement versus the existing production reset boundary.
// The private fixture calls unchanged EnemyManager code; no full-game oracle.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),sha=b=>createHash('sha256').update(b).digest('hex');
const enginePath=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/engine-th14-build.json'),engineBytes=readFileSync(enginePath),engine=JSON.parse(engineBytes);
assert.equal(Object.keys(engine.sourceHashes).length,265);
for(const [name,hash] of Object.entries(engine.sourceHashes))assert.equal(sha(readFileSync(resolve(rt,name))),hash,name);
const out=resolve(root,'artifacts/th14/staged-loader-owner',engine.sha256.slice(0,16));mkdirSync(out,{recursive:true});
const fixture=resolve(out,'fixture.cpp'),source=`#include "EnemyManager.hpp"
#include "Rng.hpp"
using namespace th11;
struct EmptyWorld final : EnemyFrameWorld { void clear_shot_targets(Enemy*) override {} };
static u32 result[10]{};
extern "C" __attribute__((export_name("observe_reset"))) const u32* observe_reset(){
 EclProgram old_program, next_program; EnemyEnvironment environment{}; EnemyCommandEnvironment commands{}; EmptyWorld world;
 Rng gameplay{}; gameplay.seed=49408;gameplay.calls=66446;environment.shared_random=&gameplay;
 EnemyManager manager(old_program,environment,commands,world);manager.total_created=299;
 result[0]=manager.total_created;result[1]=manager.count;result[2]=commands.manager==&manager;
 result[3]=manager.reset(next_program);result[4]=commands.manager==&manager;
 result[5]=manager.total_created;result[6]=manager.count;result[7]=gameplay.calls;
 result[8]=environment.th14_enemy_list==&manager.first;result[9]=gameplay.seed;return result;
}
`;
if(existsSync(fixture))assert.equal(sha(readFileSync(fixture)),sha(Buffer.from(source)));else writeFileSync(fixture,source);
const wasm=resolve(out,'owner-reset.wasm'),objects=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-I',resolve(rt,'cpp/game'),fixture,...readdirSync(objects).filter(n=>n.endsWith('.o')).map(n=>resolve(objects,n)),'-o',wasm],{cwd:rt,stdio:'inherit',windowsHide:true,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out}});
const wasmBytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(wasmBytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);
const pointer=instance.exports.observe_reset(),values=Array.from(new Uint32Array(instance.exports.memory.buffer,pointer,10));
assert.deepEqual(values,[299,0,1,1,1,1,0,66446,1,49408]);
const nativePath=resolve(out,'native.json'),nativeTool=resolve(root,'tools/th14-staged-loader-owner-native.py');
execFileSync(process.env.TH_NATIVE_PYTHON||'C:/Users/APKGG/AppData/Local/Programs/Python/Python314/python.exe',[nativeTool,'--output',nativePath],{cwd:root,stdio:'inherit',windowsHide:true});
const nativeBytes=readFileSync(nativePath),native=JSON.parse(nativeBytes);
assert(native.instructionExecutionPassed&&!native.ownerPresentAfter&&native.observableNextIdAfter===0);assert.deepEqual(native.gameplayRngAfter,[49408,0,66446]);
assert.equal(native.nativeToolSha256,sha(readFileSync(nativeTool)));assert.equal(native.imageHelperSha256,sha(readFileSync(resolve(root,'tools/th14-loading-lifecycle-evidence-check.py'))));
const production={resetReturned:true,ownerPresentAfter:!!values[4],observableNextIdAfter:values[5],enemyCountAfter:values[6],gameplayCallsAfter:values[7],enemyListPublishedAfter:!!values[8],gameplaySeedAfter:values[9],rawWords:values};
const report={diagnosticOnly:true,evidencePassed:true,boundaryEquivalent:false,productionChanged:false,completeGame:false,nativeEquivalent:false,
 sourceFilesVerified:265,sourceHashes:engine.sourceHashes,production,native,
 concreteDifferences:[{field:'ownerPresentAfter',production:true,native:false},{field:'observableNextIdAfter',production:1,native:0}],
 unchangedGameplayRng:[49408,0,66446],fixtureSource:source,fixtureSha256:sha(readFileSync(fixture)),wasmSha256:sha(wasmBytes),nativeReportSha256:sha(nativeBytes),engineBuildSha256:sha(engineBytes),toolSha256:sha(readFileSync(import.meta.filename)),
 paths:{fixture,wasm,nativeReport:nativePath},
 integrationEvidence:{existingPortReset:'GameBattle::enter_stage_transition calls EnemyManager::reset, retaining commands.manager and th14_enemy_list and resetting nextId to1.',nativeRetire:'4226c0 -> original41da20 ->422821 clears4db544; later435f66 ->4228a0 publishes a new manager and reserves nextId1.'},
 scope:'Controlled semantic boundary comparison only. Existing production EnemyManager::reset on an empty manager is compared to original EnemyManager retirement on declared synthetic empty/detached manager state. Their mismatch proves reset cannot represent owner absence during loader wait; this is not a claim that the two routines have identical API contracts. Original game instructions remain unchanged, with one explicitly owned CRT-free service and zero simulated game calls or thread time. All current265 source bindings and private fixture/WASM/native bytes retained. No C++ edits, original child game, callback masking, renderer/ordinary ending/thread/whole-game equivalence.'};
writeFileSync(resolve(root,'docs/porting/th14-staged-loader-owner-boundary-observed-oct14.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({evidencePassed:true,boundaryEquivalent:false,sourceFilesVerified:265,productionOwner:true,nativeOwner:false,productionNextId:1,nativeNextId:0,unchangedGameplayCalls:66446}));
