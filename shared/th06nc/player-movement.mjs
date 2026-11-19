import {playerInputVelocity} from './player-input.mjs';
import {integratePlayerMovement} from './player-motion.mjs';
import {rebindAnm} from './anm-rebind.mjs';
// Complete moving-player section 69066..694f6. State 1/2 gating belongs to
// the owner loop; caller owns subsequent option motion and normal ANM ticks.
export function movePlayer(state,input,{anmBank,anms,environment={},bounds}={}){
 const v=new DataView(state.buffer,state.byteOffset,state.byteLength),velocity=playerInputVelocity(input,{speed:v.getFloat32(0x7860,true),focusSpeed:v.getFloat32(0x7864,true),diagonalSpeed:v.getFloat32(0x7868,true),diagonalFocusSpeed:v.getFloat32(0x786c,true)}),previous=v.getFloat32(0x789c,true),x=velocity.x;
 v.setInt32(0x7750,velocity.direction,true);v.setUint8(0x785c,velocity.focus?1:0);
 let script=null;if(x<0&&previous>=0)script=0x421;else if(x===0&&previous<0)script=0x422;
 if(x>0&&previous<=0)script=0x423;else if(x===0&&previous>0)script=0x424;
 if(script!==null){if(!anmBank||!anms)throw Error('TH06nc: moving player needs its ANM bank');anms.set(0x78c8,rebindAnm(anmBank,script,state.subarray(0x78c8,0x79e8),{randomU16:environment.rng?()=>environment.rng.next16():null}));}
 return {velocity,position:integratePlayerMovement(state,{velocity:[velocity.x,velocity.y],bounds})};
}
