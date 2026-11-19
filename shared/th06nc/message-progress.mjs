// Message 9/11/14, original 3f82d, 3fb51 and 3fa28. Host scene switching and
// achievement persistence consume these requests outside the message VM.
export function applyMessageProgress(state,opcode,{awardAchievement=null,commitAchievements=null,getExtraCaptures=null}={}){
 const {v,environment:env}=state;
 if(opcode===9){
  v.setInt32(0x958,1,true);if((env.stageIndex??0)<6)state.rebind(0,0x648);else env.continueState=-1;
  if(!env.replayPlayback){const stage=env.stageIndex??0;if(stage>=1&&stage<=7){
   if(!awardAchievement||!commitAchievements)throw Error('TH06nc message: achievement persistence service missing');awardAchievement(`Achievement${String(stage+1).padStart(2,'0')}`);commitAchievements();
   if(stage===7&&v.getUint8(0x715)){awardAchievement('Achievement24');commitAchievements();}
  }}return 'advance';
 }
 if(opcode===11){
  env.displayScore=BigInt(env.score??0)&0xffffffffffffffffn;const stage=env.stageIndex??0,difficulty=env.difficulty??0;
  if(env.practice)env.gameState=7;
  else if(stage<5||(stage===5&&difficulty!==0))env.gameState=3;
  else if(env.replayPlayback)env.gameState=8;
  else if(difficulty===4){env.messageTaskSuspended=true;env.gameState=7;}
  else env.gameState=10;
  return 'wait';
 }
 if(opcode===14){
  if((getExtraCaptures?.()??env.extraCaptures??0)<6||(env.lifeProtection&&(env.deathCount??0)>2))return 'advance';
  env.timelineResumeRequested=true;v.setInt32(0x958,0,true);v.setUint8(0x715,1);v.setInt16(0x34,-1,true);v.setInt32(0x36b0,-1,true);v.setUint16(0x296a,1,true);state.rebind(0x5a0,0x783).bindSprite(0x782);state.rebind(0x480,0x784);v.setUint8(0x716,1);return 'return';
 }
 throw Error('TH06nc message: invalid progress opcode');
}
export function messageProgressAssetPlan(stage){
 if(!Number.isInteger(stage)||stage<1||stage>7)throw Error('TH06nc message: invalid progress stage');return [{archive:'th06CM.dat',file:'loading.anm',slot:14,base:0x648},...(stage===7?[{archive:'th06CM.dat',file:'frame_stage7.anm',slot:62,base:0x782},{archive:'th06CM.dat',file:'frame_stage7_1.anm',slot:63,base:0x783}]:[])];
}
