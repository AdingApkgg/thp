import {advanceBulletMotion} from './bullet-motion.mjs';
import {spriteLogicalSize} from './sprite-layout.mjs';
const F=Math.fround,margin=F(20); // Original 1110c7/11133: constant 30cecc.
export function advanceBullet(entry,{environment={},player=null,queryCancel=null,collision=null,spawnCancelItem=null,spawnEffect=null,soundSlots=[-1,-1,-1],soundDisabled=false,...motion}={}){
 const {v,bytes,anms}=entry,f=p=>v.getFloat32(p,true),sf=(p,x)=>v.setFloat32(p,F(x),true),clock=()=>{const n=v.getInt32(0x2c,true);v.setInt32(0x28,n,true);v.setInt32(0x2c,n+1,true);},clear=()=>bytes.fill(0);
 let state=v.getUint16(0x44,true);if(!state)return;
 if(state===5){for(let k=0;k<3;k++)sf(0x30+k*4,F(F(f(8+k*4)*F(0.5))+f(0x30+k*4)));if(anms[4].tick()){clear();return;}clock();return;}
 if(state>=2&&state<=4){const fraction=F(F(1)/F([2,2.5,3][state-2]));for(let k=0;k<3;k++)sf(0x30+k*4,F(F(fraction*f(8+k*4))+f(0x30+k*4)));if(!anms[state-1].tick()){clock();return;}v.setUint16(0x44,1,true);v.setInt32(0x2c,0,true);v.setInt32(0x28,-999,true);state=1;}
 if(state!==1){clock();return;}
 const position=()=>[f(0x30),f(0x34),f(0x38)],size=()=>[f(0x5f4),f(0x5f8),f(0x5fc)],playerPosition=player?.position??environment.playerPosition??[0,0,0];
 advanceBulletMotion(entry,{...motion,playerPosition});
 const [height,width]=spriteLogicalSize(anms[0].boundSprite),hx=F(width*F(0.5)),hy=F(height*F(0.5));
 if(F(f(0x30)+hx)<0||F(f(0x30)-hx)>384||F(f(0x34)+hy)<0||F(f(0x34)-hy)>448){
  if((v.getUint16(0x14,true)&0xdc0)||v.getUint16(0x604,true)!==0){const n=(v.getUint16(0x604,true)+1)&65535;v.setUint16(0x604,n,true);if(n>=256){clear();return;}}
  else{clear();return;}
 }else v.setUint16(0x604,0,true);
 const cancelItem=()=>{if(!spawnCancelItem)throw Error('TH06nc: bullet cancellation item service missing');spawnCancelItem({type:6,position:position(),velocity:[0,F(-2.2),0],automatic:true});};
 if(v.getUint8(0x618)===0){
  const sx=F(f(0x5f4)*F(0.5)),sy=F(f(0x5f8)*F(0.5)),rect={left:F(F(f(0x30)-sx)-margin),top:F(F(f(0x34)-sy)-margin),right:F(F(f(0x30)+sx)+margin),bottom:F(F(f(0x34)+sy)+margin)};
  if(queryCancel?.(rect)){v.setUint16(0x44,5,true);cancelItem();}
  else if(![1,2].includes((player?.state??environment.playerState??0)&255)){
   const dx=F(F(playerPosition[0])-f(0x30)),dy=F(F(playerPosition[1])-f(0x34)),radius=F(F(F(Math.min(f(0x5f8),f(0x5f4))*F(0.5))+F(20))+F(player?.hitRadius??environment.playerHitRadius??0));
   if(F(radius*radius)>F(F(dy*dy)+F(dx*dx))){
    if(!environment.grazeCountersDisabled){if((environment.stageGraze|0)<99999)environment.stageGraze=((environment.stageGraze|0)+1)|0;if((environment.totalGraze|0)<999999)environment.totalGraze=((environment.totalGraze|0)+1)|0;}
    if(!spawnEffect)throw Error('TH06nc: bullet graze effect service missing');spawnEffect({type:8,count:1,color:0xffffffff,position:playerPosition.map((x,k)=>F(F(F(x)+f(0x30+k*4))*F(0.5)))});environment.score=(BigInt(environment.score??0)+500n)&0xffffffffffffffffn;environment.inputFlags=((environment.inputFlags??0)&~64)|128;
    if(!soundDisabled&&!soundSlots.includes(30)){const i=soundSlots.findIndex(x=>x<0);if(i>=0)soundSlots[i]=30;}v.setUint8(0x618,1);
   }
  }
 }
 if(v.getUint8(0x618)===1){const result=collision?.({position:position(),size:size(),graze:true})??0;if(result){v.setUint16(0x44,5,true);if(result===2)cancelItem();}}
 anms[0].tick();clock();
}
