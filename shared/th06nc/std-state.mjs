import {rebindAnm} from './anm-rebind.mjs';
// Background initialization 785c0..78993. Resource loading is separate; this
// prepares the real ANM instances and the mutable STD copy used by native draw.
export function initializeStd(program,{anmBank}={}){
 if(!anmBank)throw Error('TH06nc STD: ANM bank required');
 const bytes=Uint8Array.from(program.bytes),file=new DataView(bytes.buffer),storage=new Uint8Array(program.primitiveCount*288),vms=[],owner=new Uint8Array(0x220),v=new DataView(owner.buffer);
 v.setInt32(0xa4,program.objectCount,true);v.setInt32(0xa0,program.primitiveCount,true);v.setBigUint64(0xa8,1n,true);v.setBigUint64(0x28,BigInt(program.instancesOffset),true);v.setBigUint64(0x1f0,BigInt(program.scriptOffset),true);v.setBigUint64(0x70,1n,true);v.setBigUint64(0x88,1n,true);
 v.setInt32(0xb0,-999,true);v.setUint32(0x40,0xff000000,true);v.setFloat32(0x44,200,true);v.setFloat32(0x48,500,true);v.setFloat32(0xc,1,true);v.setFloat32(0x18,1,true);v.setInt32(0x78,1,true);v.setInt32(0x7c,-999,true);
 for(const object of program.objects){file.setUint8(object.offset+3,1);for(const face of object.primitives){const index=vms.length,state=storage.subarray(index*288,(index+1)*288),view=new DataView(state.buffer,state.byteOffset,288);for(const p of [0x24,0x94,0xb4,0xdc])view.setInt32(p,-1,true);view.setUint16(0x34,65535,true);view.setUint16(0x108,0xf0f,true);vms.push(rebindAnm(anmBank,0x320+face.anmIndex,state));file.setUint16(face.offset+6,index,true);}}
 const overlayVm=anmBank.createVm(0,{allowMissing:true});overlayVm.state=owner.subarray(0xd0,0x1f0);overlayVm.v=new DataView(owner.buffer,0xd0,288);overlayVm.resolveSprite=id=>anmBank.sprites.get(id);
 return {program,bytes,storage,vms,owner,v,anmBank,overlayVm};
}
export function stdAssetPlan(stage){if(!Number.isInteger(stage)||stage<1||stage>7)throw Error('TH06nc STD: invalid stage');return {archive:'th06ST.dat',file:`stg${stage}bg.anm`,slot:4,base:0x320};}
