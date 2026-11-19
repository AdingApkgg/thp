import {AnmBank} from './anm-bank.mjs';
import {rebindAnm} from './anm-rebind.mjs';
const empty=new AnmBank();
// Normal replay indicator initialization 6bab0. Localization/font publication
// is an external service; retain the original 1a0-byte playback owner layout.
export function initializeReplayIndicator(playback,{anmBank,localization={},publishText=null}={}){
 const {bytes,v}=playback,vm=rebindAnm(empty,v.getUint16(0xb0,true),bytes.subarray(0x78,0x198),{resolveSprite:id=>anmBank.sprites.get(id)});vm.bindSprite(0x73f);vm.v.setInt32(0xb4,-1,true);vm.v.setUint32(0xc4,vm.v.getUint32(0xc4,true)|1,true);vm.v.setUint16(0x108,0xf0f,true);
 publishText?.(vm,{key:'EXE_REPLAY_INDICATOR',text:localization.EXE_REPLAY_INDICATOR??'EXE_REPLAY_INDICATOR',colors:[0xffffff,0,0x10101,0x40202]});
 vm.v.setUint32(0xc4,(vm.v.getUint32(0xc4,true)&~0x300)|0x400,true);v.setUint32(0x19c,v.getUint32(0x18c,true),true);vm.v.setFloat32(0xc8,4,true);vm.v.setFloat32(0xcc,428,true);vm.v.setFloat32(0xd0,0,true);v.setUint32(0x198,0,true);playback.indicatorVm=vm;return vm;
}
// Ordinary display branch 6bf52; diagnostic 0x8000 statistics are separate.
// The counter is unsigned and advances per display invocation, including pause.
export function drawReplayIndicator(playback,draw,{replay=true,setupCamera=null}={}){
 if(!playback.bytes[8]||!replay)return 1;setupCamera?.({minZ:0,maxZ:1,perspective:false});const clock=playback.v.getUint32(0x198,true),t=clock%120,alpha=(128+Math.trunc((t<60?t:120-t)*127/60))&255;
 playback.v.setUint32(0x164,((alpha<<24)|0xffffff)>>>0,true);draw(playback.indicatorVm,{snap:true,space:'screen',part:'replay-indicator',offset:0x78});playback.v.setUint32(0x198,(clock+1)>>>0,true);return 1;
}
