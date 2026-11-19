import {drawSpellFade} from './spell-practice-draw-list.mjs';
const F=Math.fround;
const pulse=frame=>{const t=(frame|0)%72;return (t<30?128+Math.trunc(Math.imul(t,127)/30):t<42?255:128+Math.trunc(Math.imul(72-t,127)/30))&255;};

// 46d40 and 4ea50: pulse opacity and selected-row gray.
export function spellPulseAlpha(frame,minimum=0){minimum&=255;return (minimum+Math.trunc(Math.imul(pulse(frame)-128,255-minimum)/127))&255;}
export function spellDifficultyColor(selected,frame){const gray=selected?(208+Math.trunc(Math.imul(pulse(frame)-128,47)/127))&255:128;return (0xff000000|gray*0x10101)>>>0;}

// 4e960: row-switch displacement and color, composed with the fade helper.
export function drawSpellTransition(vm,draw,{color=0xffffffff,ticks=0,direction=0,offsetX=0,alpha=1}={}){
 const old=vm.v.getUint32(0xec,true),remaining=(10-(ticks|0))|0;let shift=F(0);color>>>=0;
 if((ticks|0)>0&&remaining<10){
  const p=F(F(1)-F(F(remaining)/F(9))),ease=F(F(1)-F(F(p*p)*p));
  shift=F(F(F(direction|0)*F(5.333333492279053))*F(F(1)-ease));
  const opacity=Math.trunc(F(F(F(F(ease*F(.3999999761581421))+F(.6000000238418579))*F(color>>>24))+F(.5)));
  color=((opacity<<24)|(color&0xffffff))>>>0;
 }
 try{vm.v.setUint32(0xec,color,true);drawSpellFade(vm,draw,{offsetX:F(shift+F(offsetX)),offsetY:0,alpha});}finally{vm.v.setUint32(0xec,old,true);}
}

// 4f040: independent top/bottom alpha at the card-list lower boundary.
export function drawSpellListEdge(vm,draw){
 const {v}=vm;if(!vm.pointer(0x100))return;
 const sprite=vm.boundSprite;if(!sprite)throw Error('TH06nc: list-edge sprite missing');
 const height=v.getInt32(0x118,true)>0?v.getInt32(0x118,true):sprite.height;
 const screenHeight=F(F(F(F(height)*v.getFloat32(0xe4,true))*F(480))/F(1080)),top=v.getFloat32(0xcc,true);
 const opacity=y=>{const t=F(F(F(y)-F(376.77777099609375))*F(.03125));return t<=0?255:t>=1?0:Math.trunc(F(F(F(1)-t)*F(255))+F(.5))&255;};
 draw(vm,{snap:true,topAlpha:opacity(top),bottomAlpha:opacity(F(top+screenHeight))});
}
