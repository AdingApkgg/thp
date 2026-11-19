const F=Math.fround,z=F(.49),signedByte=n=>(n??0)<<24>>24;
// Original front.anm block initialization 3db56..3dbdf.
export function initializeHudFront(state){for(let i=0;i<33;i++)state.rebind(0xcc0+i*0x120,0x620+i);}
// Normal, inactive enemy-HP branch of 3fd10..3ff48. Enemy HP has a
// separate owner and must supply its own update for slot 19 when active.
export function advanceHudFrontInactive(state){for(let i=0;i<33;i++)if(i!==19)state.vm(0xcc0+i*0x120).tick();}
// Stock portion of ordinary HUD draw, 40df3..41057.
export function drawHudStock(state,draw,{inputFlags=0x2aa,force=false,lives=0,bombs=0,lifeProtection=false,deathCount=0,drawNumber=null}={}){
 const at=(offset,x,y)=>{const vm=state.vm(offset);vm.v.setFloat32(0xc8,F(x),true);vm.v.setFloat32(0xcc,F(y),true);vm.v.setFloat32(0xd0,z,true);draw(vm,{snap:true,space:'screen',part:'hud-stock',offset});};
 if((inputFlags&3)||force){
  if(lifeProtection){at(0x2fa0,711,105);if(!drawNumber)throw Error('TH06nc HUD: protected-life number service missing');drawNumber({value:deathCount|0,format:'%d',position:[796,117,z]});}
  else{let x=F(809),empty=Math.max(0,8-signedByte(lives));for(let i=0;i<empty;i++){at(0x2d60,x,118);x=F(x+F(-13));}for(let i=empty;i<8;i++){at(0x1ec0,x,118);x=F(x+F(-13));}}
 }
 if((inputFlags&12)||force){let x=F(809),empty=Math.max(0,8-signedByte(bombs));for(let i=0;i<empty;i++){at(0x2e80,x,142);x=F(x+F(-13));}for(let i=empty;i<8;i++){at(0x1fe0,x,142);x=F(x+F(-13));}}
}
