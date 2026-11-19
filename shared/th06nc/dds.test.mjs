import test from 'node:test';
import assert from 'node:assert/strict';
import {readDds} from './dds.mjs';
function fixture(bc7=false){
 const b=new Uint8Array(bc7?196:140),v=new DataView(b.buffer);
 const fields={0:0x20534444,4:124,8:bc7?0xa1007:0x100f,12:bc7?5:1,16:bc7?3:2,20:bc7?32:12,28:bc7?2:1,76:32,80:bc7?4:65,84:bc7?0x30315844:0,88:bc7?0:32,92:bc7?0:0xff0000,96:bc7?0:0xff00,100:bc7?0:255,104:bc7?0:0xff000000,108:0x1000};
 for(const [p,n]of Object.entries(fields))v.setUint32(+p,n,true);
 if(bc7){for(const [p,n]of [[128,98],[132,3],[140,1]])v.setUint32(p,n,true);b.fill(37,148);}
 else b.set([10,20,30,40,50,60,70,80,99,99,99,99],128);
 return b;
}
test('BGRA conversion preserves alpha, ignores pitch padding and handles byte offsets',()=>{
 const b=fixture(),copy=b.slice(),padded=new Uint8Array(b.length+7);padded.set(b,7);
 assert.deepEqual(readDds(padded.subarray(7)).levels[0].data,new Uint8Array([30,20,10,40,70,60,50,80]));
 assert.deepEqual(b,copy);
});
test('BC7 odd dimensions and mip levels preserve every compressed byte',()=>{
 const b=fixture(true),r=readDds(b);
 assert.equal(r.format,'BC7');assert.equal(r.compressed,true);
 assert.deepEqual(r.levels.map(l=>[l.width,l.height,l.data.length]),[[3,5,32],[1,2,16]]);
 assert.ok(r.levels.every(l=>l.data.every(x=>x===37)));
});
test('reject unsupported layouts and malformed resource extents',()=>{
 for(const mutate of [v=>v.setUint32(128,97,true),v=>v.setUint32(140,2,true),v=>v.setUint32(112,512,true),v=>v.setUint32(16,0xffffffff,true),v=>v.setUint32(28,20,true)]){
  const b=fixture(true);mutate(new DataView(b.buffer));assert.throws(()=>readDds(b),/TH06nc DDS/);
 }
 assert.throws(()=>readDds(fixture().subarray(0,139)),/truncated/);
 const b=new Uint8Array(141);b.set(fixture());assert.throws(()=>readDds(b),/trailing/);
});
