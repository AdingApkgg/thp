// Keep immutable v1 assertions and extend them for explicit manager ownership.
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
const parent=resolve(import.meta.dirname,'th14-deferred-capture-integration-check.mjs');
let source=readFileSync(parent,'utf8');
assert.equal(createHash('sha256').update(source).digest('hex'),'ce603fb93602b978817fa5f516253fe64da21102b02afc006776e3fd72909ab5');
for(const [a,b] of [['deferred-capture-integration-oct14','deferred-capture-intrinsic-oct14'],['integration-inputs.json','intrinsic-inputs.json'],['integration.wasm','intrinsic.wasm'],['th14-deferred-capture-integration-code-verified-oct14.json','th14-deferred-capture-intrinsic-code-verified-oct14.json']])source=source.replaceAll(a,b);
const replace=(a,b)=>{assert.equal(source.split(a).length,2,a);source=source.replace(a,b);};
replace('static DeferredCaptureQueueTh14 queue;static std::unique_ptr<DeferredCaptureBindingTh14> binding;','static DeferredCaptureQueueTh14& queue=animations.deferred_captures;');
replace('values[43]=queue.first_file_index();values[44]=th14_capture_queue(animations)==&queue;','values[43]=animations.first_deferred_capture_file_index();values[44]=&queue==&animations.deferred_captures;');
replace('queue={};binding.reset();binding=std::make_unique<DeferredCaptureBindingTh14>(animations,queue);','queue={};');
replace('extern "C" int unbind_case(){binding.reset();observe();return th14_capture_queue(animations)==nullptr;}',`extern "C" int headless_case(){animations.retire_deferred_captures_without_target();observe();return animations.first_deferred_capture_file_index();}
extern "C" int clear_case(){i32 before[40];std::memcpy(before,queue.slots.data(),160);animations.clear();observe();return std::memcmp(before,queue.slots.data(),160)==0;}
extern "C" int constructor_case(){AnmManager fresh;for(int i=0;i<4;++i)values[100+i]=fresh.deferred_captures.slots[i].file_index;return fresh.first_deferred_capture_file_index();}
extern "C" int first_slot_case(){const i32 files[]={-1,0,1,25};for(int i=0;i<4;++i)queue.slots[i].file_index=files[i];observe();return animations.first_deferred_capture_file_index();}`);
replace("'source_case','phase_value','unbind_case'","'source_case','phase_value','headless_case','clear_case','constructor_case','first_slot_case'");
replace("!['cpp_game_PauseMenu.cpp.o','cpp_game_PauseEnd.cpp.o'].includes(n)","!['cpp_game_PauseMenu.cpp.o','cpp_game_PauseEnd.cpp.o','cpp_game_AnmManager.cpp.o'].includes(n)");
replace("resolve(out,'source/cpp/game/PauseEnd.cpp'),...objects","resolve(out,'source/cpp/game/PauseEnd.cpp'),resolve(out,'source/cpp/game/AnmManager.cpp'),...objects");
replace('assert.equal(c.unbind_case(),1);assert.equal(words()[44],0);',`assert.equal(c.constructor_case(),-1);const newManagerFiles=words().slice(100,104);assert.deepEqual(newManagerFiles,[-1,-1,-1,-1]);
assert.equal(c.begin_case(4),1);const beforeClear=words().slice(0,40);assert.equal(c.clear_case(),1);const afterClear=words().slice(0,40);assert.deepEqual(afterClear,beforeClear);assert.equal(words()[43],0);
assert.equal(c.headless_case(),-1);const afterHeadless=words().slice(0,40);assert.deepEqual([0,10,20,30].map(i=>afterHeadless[i]),[-1,-1,-1,-1]);
assert.equal(c.first_slot_case(),-1);const firstOnlyPending=words().slice(0,40);assert.deepEqual([0,10,20,30].map(i=>firstOnlyPending[i]),[-1,0,1,25]);
assert.equal(c.headless_case(),-1);const firstOnlyAfter=words().slice(0,40);assert.deepEqual([0,10,20,30].map(i=>firstOnlyAfter[i]),[-1,-1,-1,-1]);
const intrinsicControls={newManagerFiles,beforeVmClear160Words:beforeClear,afterVmClear160Words:afterClear,afterHeadless160Words:afterHeadless,firstSlotNegativeWithOtherPending160Words:firstOnlyPending,afterAllSlotsHeadless160Words:firstOnlyAfter,explicitHeadlessRetirement:true,captureStaticRegistryUsed:false};`);
replace('applicationQueueSurvivesMenuDestruction:true,scopeBindingRemovedAtDestruction:true,','managerQueueSurvivesMenuDestruction:true,intrinsicControls,captureStaticRegistryUsed:false,');
replace("scope:'Private actual PauseMenu/PauseEnd calls", "scope:'Private intrinsic AnmManager queue appended after existing fields; private AnmManager.cpp is compiled against the new header, while enclosing GameSession objects are unused by this fixture and production needs its full rebuild. VM clear preserves all160 record bytes. Explicit headless no-target retirement consumes all4 slots while loader getter observes only slot0. No static capture registry/scope remains. Private actual PauseMenu/PauseEnd calls");
assert.equal(source.split('privateIntegrationCodeVerified:true').length,3);
source=source.replaceAll('privateIntegrationCodeVerified:true','privateIntrinsicCodeVerified:true');
source=source.replaceAll('import.meta.dirname',JSON.stringify(import.meta.dirname)).replaceAll('import.meta.filename',JSON.stringify(import.meta.filename));
await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
