import {readFileSync,writeFileSync} from 'node:fs';
import {readAnm} from '../shared/th06nc/anm.mjs';
import {AnmVm} from '../shared/th06nc/anm-vm.mjs';
import {anmQuad} from '../shared/th06nc/anm-quad.mjs';
const frames=JSON.parse(readFileSync('artifacts/th06nc/anm-vm-cases.json')),cases=[],cropResources=new Set();
for(const c of frames){
 const a=readAnm(readFileSync(c.path)),vm=new AnmVm(a,c.id);
 for(let i=0;i<c.frames.length;i+=30){
  vm.state.set(Buffer.from(c.frames[i].state,'hex'));
  for(const height of [480,1080,1440]){
   const quad=anmQuad(vm,height);if(!quad)continue;
   const angle=vm.v.getFloat32(0xa4,true);
   cases.push({name:c.name,path:c.path,id:c.id,frame:i,height,state:c.frames[i].state,angle,sin:Math.fround(Math.sin(angle)),cos:Math.fround(Math.cos(angle)),expected:Buffer.from(quad.buffer).toString('hex')});
   if(!cropResources.has(c.path)){
    const saved=vm.state.slice();
    for(const crop of [false,true])for(const rotation of [-.35,.2])for(const anchor of [0,0x100,0x200,0x300,0x400,0x500,0x600,0x700])for(const scale of [.55,-1.25]){
     vm.v.setFloat32(0xa4,rotation,true);vm.v.setUint32(0xc4,(vm.v.getUint32(0xc4,true)&~0x700)|anchor,true);vm.v.setFloat32(0xe8,scale,true);vm.v.setFloat32(0xe4,.7,true);
     vm.v.setInt32(0x114,crop?37:0,true);vm.v.setInt32(0x118,crop?19:0,true);vm.v.setInt32(0x10c,11,true);vm.v.setInt32(0x110,23,true);
     const expected=anmQuad(vm,height),angle=vm.v.getFloat32(0xa4,true);
     cases.push({name:c.name+' rotated crop='+crop,path:c.path,id:c.id,frame:i,height,state:Buffer.from(vm.state).toString('hex'),angle,cropped:crop,sin:Math.fround(Math.sin(angle)),cos:Math.fround(Math.cos(angle)),expected:Buffer.from(expected.buffer).toString('hex')});
    }
    vm.state.set(saved);cropResources.add(c.path);
   }
  }
 }
}
writeFileSync('artifacts/th06nc/anm-quad-cases.json',JSON.stringify(cases));console.log(cases.length+' quad cases');
