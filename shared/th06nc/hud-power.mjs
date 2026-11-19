import {spriteLogicalSize} from './sprite-layout.mjs';
const F=Math.fround;
// HUD owner 3dd07..3ddd6; saved metrics belong to its task wrapper.
export function initializeHudPower(state){
 const back=state.vm(0x2a00),fill=state.vm(0x2b20),marker=state.vm(0x2c40),x=fill.v.getFloat32(0xc8,true),y=fill.v.getFloat32(0xcc,true);
 back.v.setFloat32(0xc8,F(F(F(F(700)-x)+F(15.4))+back.v.getFloat32(0xc8,true)),true);
 back.v.setFloat32(0xcc,F(F(F(F(186)-y)-F(2.4))+back.v.getFloat32(0xcc,true)),true);
 for(let i=0;i<3;i++)fill.v.setUint32(0xc8+i*4,back.v.getUint32(0xc8+i*4,true),true);
 marker.v.setFloat32(0xcc,F(F(spriteLogicalSize(back.boundSprite)[0]*F(.5))+back.v.getFloat32(0xcc,true)),true);
 const sprite=fill.boundSprite;state.hudPower={spriteId:fill.v.getInt16(0x34,true),marginX:x,marginY:y,pixelWidth:F(F(sprite.x+sprite.width)-sprite.x),logicalWidth:spriteLogicalSize(sprite)[1]};return state.hudPower;
}
// 41057..413c0. Partial fill mutates the manager's shared sprite cache;
// clone that bank's sprite on write so separately loaded banks stay independent.
export function drawHudPower(state,draw,{inputFlags=0,force=false,playerPower=0,drawNumber=null}={}){
 if(!(inputFlags&0x30)&&!force)return;
 const metrics=state.hudPower;if(!metrics)throw Error('TH06nc HUD: power metrics missing');
 const at=offset=>draw(state.vm(offset),{snap:true,space:'screen',part:'hud-power',offset}),fill=state.vm(0x2b20),a=fill.v,power=playerPower&65535;at(0x2a00);
 if(power<128){
  const doubleMargin=F(metrics.marginX+metrics.marginX),availablePixels=F(metrics.pixelWidth-F(F(doubleMargin*F(1080))/F(480))),availableLogical=F(metrics.logicalWidth-doubleMargin);
  if(power!==0){
   fill.bindSprite(metrics.spriteId);const binding=fill.boundBinding,old=binding?.sprite;if(!old)throw Error('TH06nc HUD: power fill sprite missing');
   const right=F(F(F(F(metrics.marginX*F(1080))/F(480))+old.x)+F(F(F(power)*availablePixels)*F(1/128))),width=F(right-old.x),logicalWidth=F(F(width*F(480))/F(1080));
   binding.sprite={...old,width,extra:[logicalWidth,old.extra[1]]};a.setFloat32(0x3c,F(width/binding.resource.width),true);a.setFloat32(0x50,F(F(F(old.y+old.height)-old.y)/binding.resource.height),true);at(0x2b20);
  }
  const marker=state.vm(0x2c40);marker.v.setFloat32(0xc8,F(F(F(F(power)*availableLogical)*F(1/128))+F(a.getFloat32(0xc8,true)+metrics.marginX)),true);at(0x2c40);
 }else{fill.bindSprite(metrics.spriteId+1);at(0x2b20);}
 if(power<128){if(!drawNumber)throw Error('TH06nc HUD: power number service missing');drawNumber({format:'%d',value:String(power),text:String(power),position:[723,179.5,0]});}
}
