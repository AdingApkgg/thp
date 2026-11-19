import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {readAnm} from './anm.mjs';
const root=new URL('../../',import.meta.url);
const files=JSON.parse(readFileSync(new URL('artifacts/th06nc/scripts.json',root))).filter(f=>f.name.endsWith('.anm'));
test('all 125 fixed retail resources load with complete script boundaries',()=>{
 let sprites=0,scripts=0,instructions=0;
 assert.equal(files.length,125);
 for(const ref of files){
  const bytes=readFileSync(ref.path);
  assert.equal(createHash('sha256').update(bytes).digest('hex'),ref.sha256);
  const a=readAnm(bytes);sprites+=a.sprites.length;scripts+=a.scripts.length;
  instructions+=a.scripts.reduce((n,s)=>n+s.instructions.length,0);
 }
 assert.deepEqual([sprites,scripts,instructions],[2273,1062,11935]);
});
test('sprite geometry and command payloads retain retail bytes',()=>{
 const b=Uint8Array.from(readFileSync(files.find(f=>f.name==='eff00.anm').path)),copy=b.slice(),a=readAnm(b);
 assert.equal(a.textureName,'data/eff00/eff00.png');
 assert.deepEqual(a.sprites[0],{id:0,x:144,y:1,width:68,height:68,extra:[0,0]});
 assert.deepEqual(Array.from(a.scripts[0].instructions[0].args),[0,0,0,0]);
 assert.deepEqual(b,copy);
 const view=new Uint8Array(b.length+3);view.set(b,3);
 assert.deepEqual(readAnm(view.subarray(3)),a);
});
test('reject overlapping tables, crossed script boundaries and truncated resources',()=>{
 const original=readFileSync(files.find(f=>f.name==='eff00.anm').path);
 for(const mutate of [v=>v.setUint32(0,0xffffffff,true),v=>v.setUint32(64,0,true),v=>v.setUint32(28,0,true),v=>v.setUint32(56,1,true),v=>v.setUint32(64+36*4+4,1,true)]){
  const b=Uint8Array.from(original);mutate(new DataView(b.buffer));assert.throws(()=>readAnm(b),/TH06nc ANM/);
 }
 assert.throws(()=>readAnm(original.subarray(0,original.length-5)),/TH06nc ANM/);
});
