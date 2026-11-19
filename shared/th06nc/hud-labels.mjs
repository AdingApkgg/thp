// Difficulty sprite selection, 3dcc3..3dcde, after front block init.
export function initializeHudDifficulty(state,difficulty){const vm=state.vm(0x28e0);vm.bindSprite(vm.v.getInt16(0x34,true)+(difficulty|0));}
// Runtime mode flag 4f27c4, 3dcde..3dd07.
export function initializeHudModeLabel(state,enabled=false){state.v.setUint32(0x3184,(state.v.getUint32(0x3184,true)&~1)|Number(Boolean(enabled)),true);}
// Static label portion of ordinary HUD draw, 40b51..40d43.
export function drawHudLabels(state,draw,{hidden=false,inputFlags=0}={}){
 if(hidden)return inputFlags>>>0;
 for(const offset of [0x1260,0xcc0,0xde0,0x1020,0x1140,0xf00])draw(state.vm(offset),{snap:true,space:'screen',part:'hud-label',path:'rotated',offset});
 for(const offset of [0x16e0,0x1800,0x1920,0x1a40,0x1b60,0x1c80,0x1da0,0x28e0,0x30c0])draw(state.vm(offset),{snap:true,space:'screen',part:'hud-label',path:'flat',offset});
 return ((inputFlags&0xfffffeaa)|0x2aa)>>>0;
}
