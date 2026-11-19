const F=Math.fround,PI=F(Math.PI),TAU=F(2*Math.PI);
// Owner draw 6a254..6a3ff. Bomb graphics are an external callback.
export function drawPlayer(player,draw,{hideDuringRespawn=player.environment?.spellResultVisible??false,gameOver=player.environment?.gameOverRequested??false,drawBomb=null,worldOffset=[0,0]}={}){
 const {v,anms}=player;
 const invoke=(vm,snap,part,slot)=>{const a=vm.v,x=a.getFloat32(0xc8,true),y=a.getFloat32(0xcc,true);a.setFloat32(0xc8,F(x+F(worldOffset[0])),true);a.setFloat32(0xcc,F(y+F(worldOffset[1])),true);try{draw(vm,{snap,space:'screen',part,slot});}finally{a.setFloat32(0xc8,x,true);a.setFloat32(0xcc,y,true);}};
 for(let slot=0;slot<80;slot++){
  const base=0x410+slot*0x170;if(v.getUint16(base+0x10,true)!==1)continue;
  const vm=anms.get(base+0x18);if(!vm)throw Error('TH06nc: missing player shot draw ANM');
  if(vm.v.getUint16(0x88,true)){let angle=F(v.getFloat32(base+0x158,true)+PI),n=0;while(angle>PI){angle=F(angle-TAU);if(n++>16)break;}while(-PI>angle){angle=F(angle+TAU);if(n++>16)break;}vm.v.setFloat32(0xa4,F(F(Math.PI/2)-angle),true);}
  invoke(vm,false,'player-shot',slot);
 }
 if(v.getUint8(0x9ec8)){if(!drawBomb)throw Error('TH06nc: player bomb draw callback not implemented');drawBomb(player,draw);}
 const main=anms.get(0x78c8);main.v.setUint32(0xc8,v.getUint32(0x7730,true),true);main.v.setUint32(0xcc,v.getUint32(0x7734,true),true);main.v.setFloat32(0xd0,F(0.49),true);
 const state=player.state;if(gameOver||(hideDuringRespawn&&(state===1||state===2)))return;
 invoke(main,true,'player',0);
 if(!v.getUint8(0x79f8)||(state!==0&&state!==3))return;
 for(let option=0;option<2;option++){
  const vm=anms.get(0x9f38+option*0x120);vm.v.setUint32(0xc8,v.getUint32(0x7880+option*12,true),true);vm.v.setUint32(0xcc,v.getUint32(0x7884+option*12,true),true);vm.v.setFloat32(0xd0,F(0.491),true);
 }
 for(let option=0;option<2;option++)invoke(anms.get(0x9f38+option*0x120),true,'option',option);
}
