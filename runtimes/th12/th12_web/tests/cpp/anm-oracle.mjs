import {readFileSync} from 'node:fs';import {resolve} from 'node:path';
import {root} from './helpers.mjs';
import {touch} from './fixture-addresses.mjs';
import {initialiseTemplate} from './engine-block-standin.mjs';
// Real original loader/interpreter/manager. Only host allocation and GPU resource
// creation are substituted; original sprite tables and animation code execute.
export function animationOracle(m){
 let source,chunk;
 m.replace(touch(0x46a720),'memset',()=>{const sp=m.reg('ESP'),p=m.u32(sp+4),size=m.u32(sp+12);m.view(p,size).fill(m.u32(sp+8)&255);return p;});
 m.replace(touch(0x45fce4),'operator new',()=>m.allocate(m.u32(m.reg('ESP')+4)));
 m.replace(touch(0x45fd49),'operator delete',()=>0);
 m.replace(touch(0x456ad0),'diagnostic log',()=>0);
 m.replace(touch(0x46025c),'sprintf filename',()=>{const sp=m.reg('ESP'),p=m.u32(sp+4),text=m.string(m.u32(sp+12));m.write(p,Buffer.from(text+'\0'));return text.length;});
 m.replace(touch(0x458400),'read fixture file',()=>{const size=m.u32(m.reg('ESP')+4),p=m.allocate(source.length);m.write(p,source);if(size)m.u32(size,source.length);return p;},2);
 const vtable=m.allocate(0x60),texture=m.allocate(16);m.u32(texture,vtable);
 m.u32(vtable+8,m.registerImport({dll:'fixture',name:'texture release',argc:1,handler:()=>0}));
 const desc=m.registerImport({dll:'fixture',name:'texture dimensions',argc:3,handler:()=>{const out=m.u32(m.reg('ESP')+12);m.view(out,32).fill(0);m.u32(out+24,source.readUInt16LE(chunk+10));m.u32(out+28,source.readUInt16LE(chunk+12));return 0;}});m.u32(vtable+0x44,desc);
 m.replace(touch(0x453f80),'embedded texture upload',()=>{m.u32(m.reg('EDI'),texture);return 0;},2);
 m.replace(touch(0x4540a0),'blank texture allocation',()=>{m.u32(m.reg('ESI'),texture);return 0;},1);
 m.replace(touch(0x4540f0),'render target allocation',()=>{m.u32(m.reg('ESI'),texture);return 0;});
 // The original's chunk reader creates a texture per chunk. FUN_0045fbf0 is, in the decomp,
 // `(**(code **)(*DAT_004ce8f0 + 0x5c))(DAT_004ce8f0, DAT_004ce9dc, DAT_004ce9e0, 1, 1,
 // DAT_004ce9e4, 0)` - a CreateTexture - reached from FUN_004600a0 (touch(0x4545a0), the
 // fixture's own chunk reader). With the device global zero, the loader dies at pc=0x45fbff on
 // `mov ecx,[eax]` reading address 0; the tables map it (th11 0x4c3288 -> th12 0x004ce8f0),
 // and nine pushed argument dwords precede the indirect call (MEASURED, 0x45fbf0..0x45fc34; an
 // eight-word stub corrupts the loader's return address). So the fixture mounts a device object
 // with that one slot. The eighth pushed word is the texture RECORD: the function ORs 1 into
 // `[esi+0x10]` and pushes `esi`, and the chunk reader reads the record's first dword as the
 // texture interface (`0x460244 mov ecx,[edx+ebx]; 0x46024a mov edx,[ecx]; 0x460259 call
 // [edx+0x44]` - the descriptor slot this fixture already mounts). So the stub stores the
 // fixture's texture there; without that, the load stops on a null record at pc=0x46024a
 // (MEASURED: with the write-back the load runs past the call).
 const deviceVtable=m.allocate(0x100),device=m.allocate(0x20);m.u32(device,deviceVtable);
 m.u32(deviceVtable+0x5c,m.registerImport({dll:'fixture',name:'d3d device create texture',argc:9,
   handler:()=>{const record=m.u32(m.reg('ESP')+0x20);if(record>0x10000)m.u32(record,texture);return 0;}}));
 m.u32(touch(0x4c3288),device);
 const manager=m.allocate(0x7bd900),path=m.allocate(256),template=m.allocate(touch(0x434)),handle=m.allocate(4);m.view(manager,0x7bd900).fill(0);m.u32(touch(0x4c3268),manager);m.view(template,touch(0x434)).fill(0);initialiseTemplate(m,{entry:touch(0x401fd0),block:0x402551,size:touch(0x434),template});const initialized=Buffer.from(m.bytes(template,touch(0x434)));
 m.replace(touch(0x4569c0),'initialized animation allocation',()=>{const p=m.allocate(touch(0x434));m.write(p,initialized);m.u32(p+4,p);m.u32(p+16,p);return p;});
 const heap=m.heap;
 const states=()=>{const result=[];for(const offset of [0x7b562c,0x7b5634]){let node=m.u32(manager+offset),budget=20000;while(node){if(!--budget)throw Error('animation list cycle');const p=m.u32(node);result.push({id:m.u32(p),p,bytes:Buffer.from(m.bytes(p,touch(0x434)))});node=m.u32(node+4);}}return result;};
 return {
  manager,states,
  reset(){for(const off of [0x7b562c,0x7b5630,0x7b5634,0x7b5638,0x7bd888])m.u32(manager+off,0);m.f32(0x4a7948,1);for(const r of [0x4c2ef8,0x4c2f00]){m.view(r,8).fill(0);m.u32(r,12345);}},
  load(name,append=false){if(!append)m.heap=heap;source=readFileSync(resolve(root,'reference/assets',name));m.write(path,Buffer.from(name+'\0'));const original=m.call(touch(0x454190),{ecx:path,args:[manager,0]});let sprite=0,script=0,index=0;chunk=0;while(true){m.call(touch(0x4545a0),{args:[original,index++,sprite,script,m.u32(original+0x108)+chunk]});sprite+=source.readUInt16LE(chunk+4);script+=source.readUInt16LE(chunk+6);const next=source.readUInt32LE(chunk+36);if(!next)break;chunk+=next;}return {original,source,heap:m.heap};},
  spawn(resource,script,layer,mode=0){m.reg('ESI',handle);m.call([touch(0x455a00),touch(0x455df0),touch(0x455bc0),touch(0x456020)][mode],{args:[resource,script,layer]});return m.u32(handle);},
  update(overlay){m.reg('EAX',manager);m.call(overlay?touch(0x455560):touch(0x455480),{limit:50000000});},
 };
}
