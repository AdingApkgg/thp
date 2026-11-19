const F=Math.fround;
// Base timeline phase 363c2..36ec7. Caller advances the manager's clock afterwards.
export class EclTimeline {
 constructor(timeline,{spawn,openMessage,bossSlots=[],environment={}}={}){
  if(!timeline)throw Error('TH06nc ECL: missing stage timeline');
  this.timeline=timeline;this.instructions=new Map(timeline.instructions.map(i=>[i.offset,i]));this.spawn=spawn;this.openMessage=openMessage;this.bossSlots=bossSlots;this.environment=environment;
  this.cursor=null;this.frame=0;this.checkpoint=null;this.resumeRequested=false;this.messageMode=0;this.parameterWord=(environment.playerPower??0)&65535;this.messageClock=0;
  for(const ins of timeline.instructions){if(ins.time<0)break;if(ins.opcode===13){this.checkpoint=ins.offset;break;}}
 }
 runDue(){
  if((this.resumeRequested||this.environment.timelineResumeRequested)&&this.checkpoint!==null){this.cursor=this.checkpoint;this.frame=this.instructions.get(this.cursor).time;this.resumeRequested=false;this.environment.timelineResumeRequested=false;}
  this.cursor??=this.timeline.offset;const env=this.environment;let processed=0;
  for(;;){
   const ins=this.instructions.get(this.cursor);
   if(!ins){if(this.cursor!==this.timeline.end-4)throw Error('TH06nc ECL: invalid timeline offset');break;}
   if(this.frame<ins.time)break;
   if(this.frame===ins.time){
    const op=ins.opcode,a=new DataView(ins.args.buffer,ins.args.byteOffset,ins.args.byteLength);
    if(op>=0&&op<=7&&!env.suppressSpawn){
     const position=Array.from({length:3},(_,i)=>a.getFloat32(i*4,true));
     if(op>=4)for(let i=0;i<3;i++)if(position[i]<=-990){if(!env.rng)throw Error('TH06nc ECL: randomized spawn requires RNG');position[i]=F(env.rng.float01()*F((env.viewportSize??[384,448,800])[i]));}
     if(!this.spawn)throw Error('TH06nc ECL: timeline needs enemy pool service');
     const entry=this.spawn({sub:ins.arg0,position,life:(op&1)?-1:a.getInt16(12,true),item:(op&1)?-1:a.getInt16(14,true),score:(op&1)?-1:a.getInt32(16,true)});
     if(op&2)entry.v.setUint8(0xbc,entry.v.getUint8(0xbc)|0x40);
    }else if(op===8){
     if(!this.openMessage)throw Error('TH06nc ECL: timeline requires message service');
     const special=env.difficulty===0&&env.stageIndex===5&&ins.arg0===1;
     this.openMessage((env.character&255)*10+(special?3:ins.arg0));this.messageMode=3;
    }else if(op===9){
     if(!((env.messageField3b50>>>0)>0||(env.messageField36b0|0)<0)){this.frame=(this.frame-1)|0;return {blocked:true,processed};}
    }else if(op===10){
     const entry=this.bossSlots[a.getInt32(0,true)];if(!entry)throw Error('TH06nc ECL: missing reserved enemy for interrupt');entry.v.setInt32(0xf70,a.getInt32(4,true),true);
    }else if(op===11){this.parameterWord=ins.arg0&65535;env.playerPower=this.parameterWord;}
    else if(op===12){const entry=this.bossSlots[ins.arg0];if(entry&&(entry.v.getUint8(0xbc)&128)){this.frame=(this.frame-1)|0;return {blocked:true,processed};}}
   }
   this.cursor+=ins.length;processed++;
  }
  if((env.messageField36b0|0)<0)this.messageClock=(this.messageClock+1)|0;
  return {blocked:false,processed};
 }
}
