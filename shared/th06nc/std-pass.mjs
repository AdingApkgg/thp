import {rebindAnm} from './anm-rebind.mjs';
// Background render tasks 78290/78390. Their split priorities place actors
// between the base layers; the spell ANM is initialized by the front draw.
export function drawStdPass(state,pass,{setupCamera,renderState,backgroundMode,drawLayer,setFogColor,setFogRange,drawCover,drawOverlay,setTextureFactor,hideBase=false}={}){
 if(pass!==0&&pass!==1)throw Error('TH06nc STD: invalid background pass');
 const {v}=state;setupCamera?.({minZ:.5,maxZ:1});const modes=enabled=>{renderState?.({name:'depthTest',value:enabled?1:0});renderState?.({name:'cull',value:enabled?4:8});renderState?.({name:'depthWrite',value:enabled?1:0});backgroundMode?.(enabled);};modes(true);
 if(pass===0){if(v.getUint8(0x9c)){v.setUint8(0x9c,0);setFogColor?.([v.getUint8(0x42),v.getUint8(0x41),v.getUint8(0x40)]);}setFogRange?.([v.getFloat32(0x44,true),v.getFloat32(0x48,true)]);}
 if(v.getInt32(0xb8,true)<=1&&!hideBase){drawLayer?.(pass*2);drawLayer?.(pass*2+1);if(pass===1&&v.getInt32(0xb8,true)===1){modes(false);const alpha=Math.trunc(Math.imul(v.getInt32(0,true),255)/60);drawCover?.({rect:[236,16,620,464],color:(alpha<<24)>>>0});modes(true);}}
 if(pass===1){if(v.getInt32(0xb8,true)>=1){if(v.getUint8(0xbc)){v.setUint8(0xbc,0);state.overlayVm=rebindAnm(state.anmBank,0x2d3,state.owner.subarray(0xd0,0x1f0));}setTextureFactor?.({stage:1,operation:1,color:0xffffffff});drawOverlay?.(state.overlayVm,{snap:true,space:'screen'});setTextureFactor?.({stage:3,operation:3,color:0xffffffff});}setFogRange?.([1000,2000]);}
 modes(false);return 1;
}
// ECL 93/94 writes these fields at 27a2c..27a3d and spell completion.
export function beginStdSpell(state){state.v.setInt32(0xb8,1,true);state.v.setInt32(0,0,true);state.v.setUint8(0xbc,1);}
export function endStdSpell(state){state.v.setInt32(0xb8,0,true);}
