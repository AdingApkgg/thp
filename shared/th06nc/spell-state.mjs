import {createSpellRecord,materializeSpellRecord} from './spell-record.mjs';
import {spellBaseBonuses} from './spell-bonus.mjs';
// Spell commands 93/94. HUD publication is state data;
// rendering and persistence of the captured records belong to their managers.
export function createSpellState(background=null){
 const state={backgroundClock:0,hudCancelPending:0,bonusPopup:null,records:new Map(),captures:0,extraCaptures:0};
 if(background)for(const [key,offset,byte]of [['backgroundClock',0xb8,false],['backgroundFrame',0,false],['backgroundActive',0xbc,true]])Object.defineProperty(state,key,{enumerable:true,get:()=>byte?Boolean(background.v.getUint8(offset)):background.v.getInt32(offset,true),set:value=>byte?background.v.setUint8(offset,Number(Boolean(value))):background.v.setInt32(offset,value,true)});
 return state;
}
export function beginSpell(entry,args,{environment={},spellState,localization=null,soundSlots=[-1,-1,-1],soundDisabled=false,cancelBullets=null,publishSpellIntro=null}={}){
 if(!spellState)throw Error('TH06nc: spell state missing');
 const a=new DataView(args.buffer,args.byteOffset,args.byteLength),portrait=a.getInt16(0,true),id=a.getInt16(2,true),tail=args.subarray(4),end=tail.indexOf(0);
 if(end<0)throw Error('TH06nc: unterminated spell name key');const key=new TextDecoder('utf-8',{fatal:true}).decode(tail.subarray(0,end));
 const text=localization?.[key]??key;spellState.intro={portrait,scriptId:0x4c3,spriteId:0x4c6+portrait,textScriptId:0x736,key,text};publishSpellIntro?.(spellState.intro);
 if(!soundDisabled)for(let i=0;i<3;i++){if(soundSlots[i]<0){soundSlots[i]=14;break;}if(soundSlots[i]===14)break;}
 environment.spellActive=true;environment.spellCounter=1;environment.spellId=id;environment.spellBonus=spellBaseBonuses[id]??0;
 if(!cancelBullets)throw Error('TH06nc: spell start requires projectile clearing service');cancelBullets({items:true});
 spellState.backgroundClock=1;spellState.backgroundFrame=0;spellState.backgroundActive=true;
 const v=entry.v;v.setFloat32(0xa8,-0.5,true);v.setFloat32(0xac,0.5,true);v.setUint32(0xbdc,0,true);v.setUint32(0x1080,0,true);
 if(!environment.replayPlayback&&id>=0&&id<134){
  const record=spellState.records.has(id)?materializeSpellRecord(spellState.records.get(id)):createSpellRecord();record.key=key;
  const checksum=tail.subarray(0,end).reduce((sum,x)=>sum+x,0)&255;
  if(record.checksum!==checksum){record.bytes.fill(0,0x3c);record.checksum=checksum;}
  if(!environment.spellPractice){record.bonus=environment.spellBonus;if(record.attempts<9999)record.attempts++;}
  else{const index=(environment.shot&255)+(environment.character&255)*2+(environment.difficulty|0)*4;if(index<0||index>=20)throw Error('TH06nc: invalid spell practice attempt index');if(record.practiceAttempts[index]<999999999)record.practiceAttempts[index]++;}
  spellState.records.set(id,record);
 }
}
export function endSpell({environment={},spellState,bossState=null,cancelBullets=null}={}){
 if(!spellState)throw Error('TH06nc: spell state missing');
 const counter=environment.spellCounter|0;
 if(counter!==0){
  spellState.hudCancelPending=1;
  if(counter===1){
   if(!cancelBullets)throw Error('TH06nc: spell completion requires bullet conversion service');cancelBullets({convert:true});
   if(environment.spellPractice)environment.spellFinished=true;
   if(environment.spellActive){
    const base=environment.spellBonus|0,remaining=bossState?.remainingSeconds??0,bonus=(Math.trunc(Math.imul(remaining|0,base)/10)+base)|0;
    spellState.bonusPopup={previous:-999,frame:0,active:true,position:[428,16,0],value:bonus};
    environment.score=(BigInt(environment.score??0)+BigInt(bonus))&0xffffffffffffffffn;
    const id=environment.spellId>>>0;
    if(id<134&&!environment.replayPlayback){
     const record=spellState.records.get(id)??createSpellRecord();
     if(environment.spellPractice){
      const index=(environment.shot&255)+(environment.character&255)*2+(environment.difficulty|0)*4;
      if(index<0||index>=record.practiceCaptures.length)throw Error('TH06nc: invalid spell practice score index');
      if(record.practiceCaptures[index]<999999999)record.practiceCaptures[index]++;
     }else{
      if(record.captures<9999)record.captures++;
      for(let i=4;i>0;i--)record.history[i]=record.history[i-1];record.history[0]=((environment.character&255)*2+(environment.shot&255))&255;
     }
     spellState.records.set(id,record);
    }
    spellState.captures=(spellState.captures+1)|0;
    if(!environment.spellPractice&&id>=121&&id<=133){spellState.extraCaptures=(spellState.extraCaptures+1)|0;if(id===130)spellState.extraCaptures=10;}
   }
  }
  environment.spellCounter=0;
 }
 spellState.backgroundClock=0;
}
