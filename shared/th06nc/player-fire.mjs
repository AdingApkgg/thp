import {buildPlayerShot} from './player-shot-build.mjs';
// Moving-player input gate 696f4..69738.
export function acceptPlayerFireInput(player,input,{messageField=-1}={}){
 const v=player.v;if((input&1)&&messageField<0&&v.getInt32(0x40c,true)<0){v.setInt32(0x40c,0,true);v.setInt32(0x408,-999,true);}v.setUint16(0x9f34,input,true);
}
// Owner allocation/activation and fire clock, 69b7e..69c9f.
export function firePlayerShots(player,options={}){
 const {v,environment={}}=player;v.setFloat32(0x7740,-999,true);v.setFloat32(0x7744,-999,true);v.setInt32(0x7748,0,true);
 const clock=v.getInt32(0x40c,true);if(clock<0)return;
 if(clock!==v.getInt32(0x408,true)&&!(v.getUint8(0x9ec8)!==0&&(environment.character??0)===1&&(environment.shot??0)===1)){
  let index=0,stop=false;
  for(let slot=0;slot<80&&!stop;slot++){
   const base=0x410+slot*0x170;if(v.getUint16(base+0x10,true)!==0)continue;
   for(let attempts=0;attempts<64;attempts++){
    const result=buildPlayerShot(player,slot,index,clock,options);
    if(result>=0){v.setUint32(base+0xe0,v.getUint32(base+0x13c,true),true);v.setUint32(base+0xe4,v.getUint32(base+0x140,true),true);v.setFloat32(base+0xe8,0.495,true);v.setUint16(base+0x10,1,true);}
    if(result===-2||result>0){stop=true;break;}
    index++;if(result!==-1)break;
    if(attempts===63)throw Error('TH06nc: player shot record scan did not terminate');
   }
  }
 }
 const next=(clock+1)|0;v.setInt32(0x408,clock,true);v.setInt32(0x40c,next,true);
 if(next>=30||[1,2].includes(v.getUint8(0x7898)))v.setBigUint64(0x408,0xfffffffffffffc19n,true);
}
