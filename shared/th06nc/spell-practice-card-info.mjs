import {createSpellInfoPublisher,publishSpellInfoHeading,spellBossKeys} from './spell-practice-info-text.mjs';
import {spellPracticeViewport} from './spell-practice-table.mjs';

const F=Math.fround,metric=value=>F(F(F(value)*F(480))/F(1080));
const width=vm=>metric(vm.v.getInt32(0x114,true)),height=vm=>metric(vm.v.getInt32(0x118,true));
const scaledWidth=(vm,scale)=>F(F(F(F(vm.v.getInt32(0x114,true))*F(scale))*F(480))/F(1080));
const place=(vm,x,y,scale=1)=>{for(const [p,v]of [[0xc8,x],[0xcc,y],[0xd0,0],[0xe4,scale],[0xe8,scale]])vm.v.setFloat32(p,v,true);};

// Card-list/difficulty information in 50ab7..52362. A real synchronous text
// publisher is required: subsequent layout reads the VM's published metrics.
export function refreshSpellPracticeCardInfo(group,state,{table,records,character,shot,localization={},publishText}={}){
 if(![29,30].includes(state.state))throw Error('TH06nc: card/difficulty info owner required');
 const profile=(character&255)*2+(shot&255),localize=key=>localization[key]??key,publish=createSpellInfoPublisher(group,publishText);
 publishSpellInfoHeading(publish,state,profile,localization);
 for(const [offset,id,suffix,x]of [[0x16a50,0x738,'SPELLCARD_COLUMN',56.888893127441406],[0x16c90,0x73a,'BY_DIFFICULTY',249.33334350585938]]){
  const key='EXE_SPELL_PRACTICE_'+suffix;publish(offset,id,localize(key),{key,x,y:102.55555725097656});
 }
 const viewport=spellPracticeViewport(table,state.spellStage,state.spellOrder,state.spellScroll);
 const userKey='EXE_SPELL_PRACTICE_USER',user=publish(0x16db0,0x73b,localize(userKey),{key:userKey,scale:.7});
 const userX=F(F(F(F(F(F(user.v.getInt32(0x114,true))*F(.7))*F(480))/F(1080))+F(74.55555725097656))+F(5.333333492279053));
 const attempted=row=>row.id<134&&Boolean(records.get(row.id)?.attempts);
 const bossName=(stage,midboss)=>{
  const unlocked=table.some(r=>r.stageIndex===stage&&Boolean(r.midboss)===Boolean(midboss)&&attempted(r));
  const key=!unlocked?'EXE_UNKNOWN_SPELLCARD_NAME':stage===5&&midboss?'EXE_BOSS_NAME_SAKUYA':stage===6&&midboss?'EXE_BOSS_NAME_PATCHOULI':spellBossKeys[stage];
  return localize(key);
 };
 const slotKey='EXE_SPELL_PRACTICE_SLOT_FMT',slotText=number=>localize(slotKey).replace(/%d/,String(number));
 for(let i=0;i<viewport.visible;i++){
  const order=viewport.start+i,baseY=F(F(F(i)*F(32))+F(120.77777862548828));
  publish(0x16ed0+i*288,0x73c+i,slotText(order+1),{key:slotKey,x:63.55555725097656,y:F(baseY+F(1.5555554628372192))});
  const row=table.find(r=>r.stageIndex===state.spellStage&&r.order===order),text=row?bossName(state.spellStage,Boolean(row.midboss)):'';
  publish(0x177d0+i*288,0x744+i,text,{x:userX,y:F(baseY+F(18.88888931274414)),scale:.7,color:0xe0ffff});
 }
 publish(0x180d0,0x74c,viewport.end<viewport.count?slotText(viewport.end+1):'',{x:63.55555725097656,y:378.33331298828125});
 const sprite=group.slots.get(0x1a178)?.boundSprite;if(!sprite)throw Error('TH06nc: spell-info panel sprite required');
 const right=F(metric(sprite.width)+F(243.11111450195312));state.infoRecordGap??=0;
 for(let i=0;i<(state.spellStage===6?1:4);i++){
  const difficulty=state.spellStage===6?4:i,row=table.find(r=>r.stageIndex===state.spellStage&&r.order===state.spellOrder&&r.difficulty===difficulty)??null;
  const baseY=F(F(F(i)*F(76.66666412353516))+F(117.77777862548828)),line=F(baseY+F(26.77777862548828)),nameY=F(line-F(3.555555582046509));
  const numberOffset=0x18f70+i*288,nameOffset=0x18670+i*288,numberSprite=0x759+i,nameSprite=0x751+i;
  if(!row){
   publish(numberOffset,numberSprite,'',{x:272.5555725097656,y:nameY});
   const vm=publish(nameOffset,nameSprite,'------',{x:272.5555725097656,y:nameY}),actual=width(vm),available=F(right-F(272.5555725097656));
   if(actual>available&&actual>0){const scale=F(available/actual);vm.v.setFloat32(0xe4,scale,true);vm.v.setFloat32(0xe8,scale,true);}
   continue;
  }
  const number='No.'+String(row.id+1).padStart(3,'0'),name=localize(attempted(row)?row.name:'EXE_UNKNOWN_SPELLCARD_NAME');
  let numVm=publish(numberOffset,numberSprite,number),numWidth=width(numVm),numHeight=height(numVm);
  let nameVm=publish(nameOffset,nameSprite,name),nameWidth=width(nameVm);
  numVm=publish(numberOffset,numberSprite,number+' '+name);
  const combined=width(numVm),sum=F(numWidth+nameWidth),excess=combined>sum?F(F(combined-numWidth)-nameWidth):0;
  const nameX=F(F(F(F(numWidth*F(.8))+F(272.5555725097656))+excess)+F(5.333333492279053));
  numVm=publish(numberOffset,numberSprite,number,{x:272.5555725097656,y:F(F(F(numHeight*F(.19999998807907104))+line)-F(3.555555582046509)),scale:.8});
  nameVm=publish(nameOffset,nameSprite,name,{x:nameX,y:nameY});
  const nameAvailable=F(right-nameX),nameActual=width(nameVm);
  if(nameActual>nameAvailable&&nameActual>0){const scale=F(nameAvailable/nameActual);nameVm.v.setFloat32(0xe4,scale,true);nameVm.v.setFloat32(0xe8,scale,true);nameVm.v.setFloat32(0xcc,F(nameY+F(height(nameVm)*F(F(1)-scale))),true);}
  const record=records.get(row.id),index=difficulty*4+profile,score=record?new DataView(record.bytes.buffer,record.bytes.byteOffset,record.bytes.byteLength).getBigUint64(0x40+index*8,true):0n;
  const bestKey='EXE_SPELL_PRACTICE_BEST_SCORE';publish(0x18af0+i*288,0x755+i,localize(bestKey)+' '+score.toString().padStart(9,'0'),{key:bestKey,x:290.3333435058594,y:F(baseY+F(45)),scale:.8});
  const captureText=localize('EXE_SPELL_PRACTICE_CAPTURED')+' '+(record?.practiceCaptures[index]??0)+'/'+(record?.practiceAttempts[index]??0),mainText=localize('EXE_SPELL_PRACTICE_MAIN_GAME')+' '+(record?.captures??0)+'/'+(record?.attempts??0),statsY=F(baseY+F(58));
  const captureOffset=0x181f0+i*288,mainOffset=0x193f0+i*288,captureSprite=0x74d+i,mainSprite=0x75d+i;
  const capVm=publish(captureOffset,captureSprite,captureText,{x:290.3333435058594,y:statsY,scale:.8}),capWidth=scaledWidth(capVm,.8);
  let mainVm=publish(mainOffset,mainSprite,mainText,{x:290.3333435058594,y:statsY,scale:.8}),mainWidth=scaledWidth(mainVm,.8);
  if(state.infoRecordGap<=0){
   mainVm=publish(mainOffset,mainSprite,captureText+'  '+mainText,{x:290.3333435058594,y:statsY,scale:.8});
   const together=scaledWidth(mainVm,.8),parts=F(mainWidth+capWidth);state.infoRecordGap=together>parts?F(F(together-capWidth)-mainWidth):0;
   mainVm=publish(mainOffset,mainSprite,mainText,{x:290.3333435058594,y:statsY,scale:.8});
  }
  const firstSpan=F(scaledWidth(capVm,capVm.v.getFloat32(0xe8,true))+state.infoRecordGap),total=F(scaledWidth(mainVm,.8)+firstSpan),available=F(right-F(290.3333435058594));let fit=F(1);
  if(total>available&&total>0){fit=F(available/total);for(const vm of [capVm,mainVm])for(const p of [0xe4,0xe8])vm.v.setFloat32(p,F(fit*vm.v.getFloat32(p,true)),true);}
  mainVm.v.setFloat32(0xc8,F(F(fit*firstSpan)+F(290.3333435058594)),true);
 }
}
