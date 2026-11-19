const F=Math.fround;
// Dialog portion of HUD draw 3d023..3d0ad; lower draw applies visibility flags.
export function drawMessage(state,draw,{worldOffset=[0,0]}={}){
 const id=state.v.getInt32(0x36b0,true);if(id<0||(state.environment.stageIndex===6&&(id===1||id===11)))return;
 for(const [offset,part,slot]of [[0x3428,'portrait',0],[0x3548,'portrait',1],[0x3b60,'message-frame',0],[0x36b8,'message-line',0],[0x37d8,'message-line',1],[0x3910,'message-extra',0],[0x3a30,'message-extra',1]]){
  const vm=state.vm(offset),v=vm.v,x=v.getFloat32(0xc8,true),y=v.getFloat32(0xcc,true);v.setFloat32(0xc8,F(x+F(worldOffset[0])),true);v.setFloat32(0xcc,F(y+F(worldOffset[1])),true);try{draw(vm,{snap:true,space:'screen',part,slot});}finally{v.setFloat32(0xc8,x,true);v.setFloat32(0xcc,y,true);}
 }
}
