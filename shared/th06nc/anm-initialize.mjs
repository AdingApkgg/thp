import {rebindAnm} from './anm-rebind.mjs';
// Convenience initializer 2760, distinct from the selective 1da0 setter.
export function initializeAnm(bank,id,state,options={}){
 const v=new DataView(state.buffer,state.byteOffset,state.byteLength);
 v.setBigUint64(0xc8,0n,true);v.setUint32(0xd0,0,true);v.setBigUint64(0x18,0n,true);v.setUint32(0x20,0,true);v.setUint16(0x108,0xf0f,true);v.setUint32(0xc4,v.getUint32(0xc4,true)&~0xc0,true);
 return rebindAnm(bank,id,state,options);
}
