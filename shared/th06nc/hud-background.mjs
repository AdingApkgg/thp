// Ordinary HUD frame initialization 3dbdf..3dcbf and draw task 415d0.
export const hudFrameAsset={archive:'th06CM.dat',file:'frame.anm',slot:54,base:0x779};
export function initializeHudBackground(state){
 state.rebind(0x31e0,0x779);state.rebind(0x3300,0x77a);
 state.v.setFloat32(0x33c8,213,true);state.v.setFloat32(0x33cc,0,true);
}
export function advanceHudBackground(state){state.vm(0x31e0).tick();}
export function drawHudBackground(state,draw,{setupCamera=null,drawCover=null,hidden=false,color=0}={}){
 setupCamera?.({minZ:0,maxZ:1});if(hidden)return;
 const frame=state.vm(0x31e0);frame.v.setBigUint64(0xc8,0n,true);frame.v.setFloat32(0xd0,1,true);
 for(const offset of [0x31e0,0x480,0x5a0,0x3300])draw(state.vm(offset),{snap:true,space:'screen',part:'hud-background',offset});
 drawCover?.({rect:[236,16,620,464],color:(color|0xff000000)>>>0});
}
