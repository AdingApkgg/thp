import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {readAnm} from './anm.mjs';
import {AnmBank} from './anm-bank.mjs';
const resource=()=>readAnm(readFileSync(new URL('../../runtimes/th06nc/artifacts/scripts/th06TL.dat/title00.anm',import.meta.url)));
test('caller base links local sprite references into global table',()=>{
 const a=resource(),bank=new AnmBank();bank.load(a,536);
 const vm=bank.createVm(536);vm.tick();
 assert.equal(vm.v.getUint16(0x34,true),536);
 assert.equal(vm.v.getUint16(0x38,true),536);
 assert.equal(vm.boundResource,a);assert.equal(vm.boundSprite,a.sprites[0]);
});
test('sprite-only overlay replaces binding while original script stays available',()=>{
 const a=resource(),overlay={...a,textureName:'overlay',sprites:a.sprites.map(s=>({...s,x:s.x+1})),scripts:[]};
 const bank=new AnmBank();bank.load(a,536);bank.load(overlay,536);
 const vm=bank.createVm(536);vm.tick();assert.equal(vm.boundResource,overlay);
 assert.equal(vm.script,a.scripts[0]);
 assert.throws(()=>bank.createVm(999),/missing global script/);
});
test('existing VM follows slot overwrite and unload invalidates its binding',()=>{
 const a=resource(),b={...a,textureName:'replacement',sprites:a.sprites.map(s=>({...s,x:s.x+1}))};
 const bank=new AnmBank();bank.load(a,536,{slot:25});const vm=bank.createVm(536);vm.tick();
 bank.load(b,536,{slot:25});assert.equal(vm.boundResource,b);assert.equal(vm.boundSprite,b.sprites[0]);
 bank.unload(25);assert.equal(vm.boundBinding.active,false);assert.equal(vm.boundResource,null);
 assert.throws(()=>bank.createVm(536),/missing global script/);
});
