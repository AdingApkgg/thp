const F=Math.fround;
// Typed aliases for the actual three 28-byte HUD popup records. Publishers
// keep their existing object interface; updates/draws observe the same bytes.
export function bindHudPopup(state,target,property,offset){
 const v=state.v;Object.defineProperty(target,property,{enumerable:true,configurable:true,get:()=>v.getUint8(offset+8)?{previous:v.getInt32(offset,true),frame:v.getInt32(offset+4,true),active:true,position:[0,1,2].map(i=>v.getFloat32(offset+12+i*4,true)),value:v.getInt32(offset+24,true)}:null,set:popup=>{if(!popup){v.setUint8(offset+8,0);return;}v.setInt32(offset,popup.previous,true);v.setInt32(offset+4,popup.frame,true);v.setUint8(offset+8,Number(Boolean(popup.active)));popup.position.forEach((x,i)=>v.setFloat32(offset+12+i*4,F(x),true));v.setInt32(offset+24,popup.value,true);}});
}
const bonusText=value=>'BONUS '+String(value|0).padStart(8,' ');
// Ordinary HUD popup update, 3fffb..401a0.
export function advanceHudNotifications(state){
 const v=state.v,timer=(offset,limit)=>{const frame=v.getInt32(offset+4,true);if(frame>=limit)v.setUint8(offset+8,0);v.setInt32(offset,frame,true);v.setInt32(offset+4,(frame+1)|0,true);};
 if(v.getUint8(0x6c8)){const frame=v.getInt32(0x6c4,true),width=F(F(bonusText(v.getInt32(0x6d8,true)).length)*F(12));let x=F(F(F(F(384)-width)*F(.5))+F(236));if(frame<30)x=F(F(F(F(x-F(620))*F(frame))/F(30))+F(620));v.setFloat32(0x6cc,x,true);timer(0x6c0,250);}
 if(v.getUint8(0x6e4)){const frame=v.getInt32(0x6e0,true),x=frame<30?F(F(620)-F(F(F(frame)*F(312))/F(30))):F(308);v.setFloat32(0x6e8,x,true);timer(0x6dc,180);}
 if(v.getUint8(0x700))timer(0x6f8,280);
}
// Notification portion of the HUD draw owner, 3d0cd..3d34d. These requests
// use gameplay clipping, while their positions remain logical HUD coordinates.
export function drawHudNotifications(state,drawText){
 const v=state.v,position=offset=>[0,1,2].map(i=>v.getFloat32(offset+i*4,true));
 if(v.getUint8(0x6c8))drawText({text:bonusText(v.getInt32(0x6d8,true)),position:position(0x6cc),color:0xffffff80,camera:1});
 if(v.getUint8(0x6e4))drawText({text:'Full Power Mode!!',position:position(0x6e8),color:0xffc0b0ff,camera:1});
 if(v.getUint8(0x700)){
  v.setFloat32(0x704,326,true);v.setFloat32(0x708,80,true);drawText({text:'Spell Card Bonus!',position:position(0x704),color:0xffff0000,camera:1});
  v.setFloat32(0x708,F(v.getFloat32(0x708,true)+F(16)),true);const text='+'+String(v.getInt32(0x710,true)),width=F(F(F(text.length)*F(12))*F(2)),x=F(F(F(F(384)-width)*F(.5))+F(236));v.setFloat32(0x704,x,true);drawText({text,position:position(0x704),scale:[2,2],color:0xffff8080,camera:1});
 }
}
