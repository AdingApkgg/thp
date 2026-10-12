import {touch} from './fixture-addresses.mjs';
import test from'node:test';import assert from'node:assert/strict';import{core,oracle,memory,report}from'./helpers.mjs';
test('TH11 keyboard mapper preserves original numpad and menu shortcuts',async()=>{
 const c=await core(),m=await oracle(),keys=new Uint8Array(256),p=c.allocate(256);let checks=0;
 m.u32(0x4c3d94,1);m.u32(touch(0x4c3810),0);
 m.u32(0x48b244,m.registerImport({dll:'keyboard',name:'GetKeyboardState',argc:1,handler:()=>{m.write(m.u32(m.reg('ESP')+4),keys);return 1;}}));
 m.replace(touch(0x457270),'controller input boundary',()=>m.reg('ECX'));m.replace(touch(0x459b50),'repeat sampler boundary',()=>0);
 try{for(let sample=0;sample<512;++sample){keys.fill(0);if(sample<256)keys[sample]=128;else for(let i=0;i<256;++i)if(((Math.imul(i+sample,14379)>>>3)&7)===0)keys[i]=128;
  memory(c,p,256).set(keys.map(n=>n?1:0));assert.equal(c.keyboard_input(p),m.call(touch(0x4576b0)),'key sample '+sample);++checks;
 }report('keyboard-input',{passed:true,checks,scope:'Actual native 4576b0 virtual-key sampler, every single key plus simultaneous combinations; controller and repeat sampler isolated.'});
 }finally{c.release(p);m.close();}
});
