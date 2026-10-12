import assert from 'node:assert/strict';
import {openBrowserSaveStore} from '../runtimes/th12/th12_web/sdl-runtime/browser-save-store.mjs';
// Exercise asynchronous failure/retry and overlapping save requests. The real
// browser reload is a separate gate; this fake does not claim IndexedDB proof.
const events=[],callbacks=[];let captureOK=true;
const core={IDBFS:{},FS:{
 mkdirTree:p=>events.push(['mkdir',p]),
 mount:(type,options,p)=>events.push(['mount',p]),
 symlink:(from,to)=>events.push(['link',from,to]),
 syncfs:(populate,done)=>{events.push(['sync',populate]);callbacks.push(done);}
},_th11_save_scores:()=>{events.push(['capture']);return +captureOK;}};
const opening=openBrowserSaveStore(core,14);
assert.deepEqual(events,[['mkdir','/savesth14'],['mount','/savesth14'],['sync',true]]);
callbacks.shift()(null);const store=await opening;
assert.deepEqual(events.slice(-2),[['mkdir','/savesth14/replay'],['link','/savesth14','/save']]);
await store.save();assert.equal(callbacks.length,0,'never capture an uninitialized engine');store.activate();
const first=store.save(),second=store.save();await Promise.resolve();
assert.equal(callbacks.length,1,'overlapping flushes are serialized');
callbacks.shift()(Error('controlled transaction failure'));await assert.rejects(first,/transaction failure/);
await Promise.resolve();assert.equal(callbacks.length,1,'next queued flush retries');callbacks.shift()(null);await second;
captureOK=false;await assert.rejects(store.save(),/写入/);assert.equal(callbacks.length,0,'failed encoding must not flush');
captureOK=true;const retry=store.save();await Promise.resolve();callbacks.shift()(null);await retry;
const broken=openBrowserSaveStore(core,14);callbacks.shift()(Error('controlled load failure'));await assert.rejects(broken,/load failure/);
await assert.rejects(openBrowserSaveStore(core,11),/不受支持/);
console.log('PASS TH14 save mount/load ordering, pre-init guard, serialized flushes, visible failures and retry');
