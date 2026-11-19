const F=Math.fround;
export function initializeSpellNameHud(state){state.rebind(0x3da0,0x638);state.v.setUint16(0x940,0xf0f,true);}
// Opcode 93 HUD publication, 2787d..279a3. Sound 14 is queued by
// beginSpell's following core block, rather than by this publication service.
export function publishSpellName(state,{portrait,key,text},{publishText,localization=null}={}){
 if(state.bytes.length<0x4228||!publishText)throw Error('TH06nc HUD: spell portrait/text service missing');
 state.rebind(0x4108,0x4c3).bindSprite(0x4c6+((portrait<<16)>>16));state.rebind(0x838,0x736);
 publishText({offset:0x838,key,text:text??localization?.[key]??key,colors:[0xfff0f0,0,0x10101,0x40202]});
}
export function finishSpellName(state){state.v.setInt16(0x8c2,1,true);}
// Contiguous ordinary HUD update, 3ffa4..3ffd2.
export function advanceSpellName(state){state.vm(0x4108).tick();state.vm(0x838).tick();}
// Ordinary HUD name-strip/text draw, 41a29..41abb.
export function drawSpellNameText(state,draw,{worldOffset=[0,0]}={}){
 const text=state.vm(0x838);if(!(text.v.getUint8(0xc4)&1))return;
 const bar=state.vm(0x3da0),b=bar.v,s=bar.boundSprite;if(!s)throw Error('TH06nc HUD: spell-name strip missing');
 for(let i=0;i<3;i++)b.setUint32(0xc8+i*4,text.v.getUint32(0xc8+i*4,true),true);
 b.setFloat32(0xc8,F(b.getFloat32(0xc8,true)+F(7.111111164093018)),true);b.setFloat32(0xe8,F(F(F(text.v.getInt32(0x114,true))+F(32))/F(F(s.x+s.width)-s.x)),true);
 for(const [vm,offset,part]of [[bar,0x3da0,'spell-name-strip'],[text,0x838,'spell-name']]){const v=vm.v,x=v.getFloat32(0xc8,true),y=v.getFloat32(0xcc,true);v.setFloat32(0xc8,F(x+F(worldOffset[0])),true);v.setFloat32(0xcc,F(y+F(worldOffset[1])),true);try{draw(vm,{snap:true,space:'screen',part,offset});}finally{v.setFloat32(0xc8,x,true);v.setFloat32(0xcc,y,true);}}
}
