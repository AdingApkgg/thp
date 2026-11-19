const F=Math.fround;
const thresholds=[8,16,32,48,64,80,96,128,999],chainScores=[10,20,30,40,50,60,70,80,90,100,200,300,400,500,600,700,800,900,1000,2000,3000,4000,5000,6000,7000,8000,9000,10000,11000,12000,51200];
const level=power=>{let n=0;while(power>=thresholds[n]&&n<thresholds.length)n++;return n;};
// Item type branches 42d5a..43771. Pickup rectangle testing belongs to owner.
export function collectItem(item,{environment:env={},popups,cancelBullets=null,soundSlots=[-1,-1,-1],soundDisabled=false,pointValue=0}={}){
 const {v}=item,type=v.getInt8(0x34),position=Array.from({length:3},(_,k)=>v.getFloat32(0x10+k*4,true));
 const add=value=>{env.score=(BigInt(env.score??0)+BigInt(value))&0xffffffffffffffffn;};
 const popup=(value,color=0xffffffff,small=false)=>{if(!popups)throw Error('TH06nc: item collection needs score popup pool');(small?popups.publishSmall({position,value}):popups.publish({position,value,color}));};
 const sound=id=>{if(soundDisabled||soundSlots.includes(id))return;const i=soundSlots.findIndex(x=>x<0);if(i>=0)soundSlots[i]=id;};
 const fullPower=()=>{if(!cancelBullets)throw Error('TH06nc: full-power bullet conversion service missing');cancelBullets({items:true});env.powerPopup={previous:-999,frame:0,active:true,position:[620,232,0],value:0};};
 const oldPower=(env.playerPower??0)&65535;
 if(type===0||type===2){
  if(oldPower>=128){const chain=Math.min(((env.powerItemChain??0)+(type===0?1:8))&255,30);env.powerItemChain=chain;const value=chainScores[chain];add(value);popup(value,value>=12800?0xffffff00:0xffffffff);}
  else{
   const before=level(oldPower);if(type===0)env.powerItemChain=0;env.playerPower=Math.min(128,oldPower+(type===0?1:8));if(env.playerPower>=128)fullPower();add(10);env.inputFlags=((env.inputFlags??0)&~16)|32;
   if(level(env.playerPower)!==before){popup(-1,0xff80c0ff);sound(31);}else popup(10);
  }
 }else if(type===1){
  const y=Math.trunc(F(position[1])),difficulty=env.difficulty??0;let maximum=null;
  if(difficulty===0||difficulty===1){maximum=100000;pointValue=y<128?maximum:Math.imul(728-y,100);}
  else if(difficulty===2){maximum=150000;pointValue=y<128?maximum:(123040-Math.imul(y,180))|0;}
  else if(difficulty===3){maximum=200000;pointValue=y<128?maximum:(184560-Math.imul(y,270))|0;}
  else if(difficulty===4){maximum=300000;pointValue=y<128?maximum:Math.imul(628-y,400);}
  if(maximum!==null)popup(pointValue,pointValue>=maximum?0xffffff00:0xffffffff);
  env.pointStageCount=((env.pointStageCount??0)+1)&65535;env.pointTotalCount=((env.pointTotalCount??0)+1)&65535;add(pointValue|0);env.inputFlags=((env.inputFlags??0)&~256)|512;
 }else if(type===3){
  if(((env.bombs??0)<<24>>24)<8){env.bombs=((env.bombs??0)+1)&255;env.inputFlags=((env.inputFlags??0)&~4)|8;}
 }else if(type===4){
  if(oldPower<128){fullPower();sound(31);popup(-1,0xff80c0ff);}add(1000);env.playerPower=128;popup(1000);env.inputFlags=((env.inputFlags??0)&~16)|32;
 }else if(type===5){
  if(env.lifeProtection)env.deathCount=((env.deathCount??0)-1)|0;else if(((env.lives??0)<<24>>24)<8){env.lives=((env.lives??0)+1)&255;env.inputFlags=((env.inputFlags??0)&~1)|2;}sound(28);
 }else if(type===6){
  const value=env.grazeCountersDisabled?100:Math.imul((Math.trunc((env.stageGraze??0)/3)+50)|0,10);add(value);popup(value,0xffffffff,true);
 }
 v.setUint8(0,0);return pointValue|0;
}
