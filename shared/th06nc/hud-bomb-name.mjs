import {queueSound} from './sound-queue.mjs';
const F=Math.fround;
function drawAt(vm,draw,options,worldOffset){const v=vm.v,x=v.getFloat32(0xc8,true),y=v.getFloat32(0xcc,true);v.setFloat32(0xc8,F(x+F(worldOffset[0])),true);v.setFloat32(0xcc,F(y+F(worldOffset[1])),true);try{draw(vm,options);}finally{v.setFloat32(0xc8,x,true);v.setFloat32(0xcc,y,true);}}
export const hudFrontAsset={archive:'th06CM.dat',file:'front.anm',slot:13,base:0x620};
export function initializeBombNameHud(state){state.rebind(0x3c80,0x637);}
// Native 3d370; full HUD allocation is 4228 bytes (3d550).
export function publishBombName(state,{key,resourceSlot},{publishText,localization=null,soundSlots=[-1,-1,-1],soundDisabled=false}={}){
 if(state.bytes.length<0x4228)throw Error('TH06nc HUD: bomb name requires full owner storage');
 const binding=state.anmBank.slots.get(resourceSlot);if(!binding||!publishText)throw Error('TH06nc HUD: bomb portrait/text service missing');
 state.rebind(0x3fe8,0x4c1).bindSprite(binding.base+1);state.rebind(0x718,0x735);
 publishText({offset:0x718,key,text:localization?.[key]??key,colors:[0xf0f0ff,0,0x10101,0x40202]});
 state.environment.bombCaptionMode=3;queueSound(soundSlots,14,{disabled:soundDisabled});
}
export function finishBombName(state){state.v.setInt16(0x7a2,1,true);}
// Contiguous part of ordinary HUD priority-12 update, 3ff76..3ffa4.
export function advanceBombName(state){state.vm(0x3fe8).tick();state.vm(0x718).tick();}
// Portrait draw task 3cca0; second slot belongs to the enemy spell portrait.
export function drawHudPortraits(state,draw,{setupCamera=null,worldOffset=[0,0]}={}){
 const offsets=[0x3fe8,0x4108];if(offsets.some(offset=>state.v.getUint8(offset+0xc4)&1))setupCamera?.({minZ:0,maxZ:.5});
 for(const offset of offsets)if(state.v.getUint8(offset+0xc4)&1)drawAt(state.vm(offset),draw,{snap:true,space:'screen',part:offset===0x3fe8?'bomb-portrait':'spell-portrait',slot:offset===0x3fe8?0:1,offset},worldOffset);
}
// Name strip and text, ordinary HUD draw 41987..41a29.
export function drawBombNameText(state,draw,{worldOffset=[0,0]}={}){
 const text=state.vm(0x718);if(!(text.v.getUint8(0xc4)&1))return;
 const bar=state.vm(0x3c80),b=bar.v,s=bar.boundSprite;if(!s)throw Error('TH06nc HUD: bomb-name strip missing');
 for(let k=0;k<3;k++)b.setUint32(0xc8+k*4,text.v.getUint32(0xc8+k*4,true),true);
 b.setFloat32(0xc8,F(b.getFloat32(0xc8,true)-F(7.111111164093018)),true);b.setFloat32(0xe8,F(F(F(text.v.getInt32(0x114,true))+F(32))/F(F(s.x+s.width)-s.x)),true);
 drawAt(bar,draw,{snap:true,space:'screen',part:'bomb-name-strip',slot:0,offset:0x3c80},worldOffset);drawAt(text,draw,{snap:true,space:'screen',part:'bomb-name',slot:0,offset:0x718},worldOffset);
}
