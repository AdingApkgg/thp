import {queryEclLife} from './ecl-life-query.mjs';
import {queueSound} from './sound-queue.mjs';
import {initializeEnemyLifeHud} from './hud-enemy-life.mjs';
const F=Math.fround,colors=[0xffff8fa3,0xffe62f4f,0xffa855e0];
// Dirty-segment resolution inside 40789..408fd. The first registered boss
// supplies its current ECL PC and future life callback chain.
export function resolveEnemyLifeSegments(state,bossState,{entry=null,program=null,difficulty=0,spellCounter=0}={}){
 if(!bossState.dirty)return;
 bossState.dirty=false;const life=state.hudEnemyLife??initializeEnemyLifeHud(state);
 if(!entry||entry.v.getInt32(0x238,true)<=0)return;
 life.segments.fill(0);
 const v=entry.v,maximum=v.getInt32(0x238,true),query=(sub,options={})=>program?queryEclLife(program,sub,{difficulty,...options}):{containsSpell:false,nextThreshold:-1,nextSubroutine:-1};
 let containsSpell=(spellCounter|0)!==0;
 if(!containsSpell){const threshold=v.getInt32(0xa0,true),pc=Number(v.getBigUint64(0x88,true));containsSpell=query(v.getUint16(0x80,true),{startOffset:pc||null,excludeSubroutine:threshold>0?v.getInt32(0xa4,true):-1}).containsSpell;}
 let index=0;if(containsSpell){life.segments[0]=1;index=1;}
 let threshold=v.getInt32(0xa0,true),next=v.getInt32(0xa4,true);
 while(threshold>0&&next>=0&&index<3){const metadata=query(next);if(!metadata.containsSpell)break;const ratio=F(F(threshold)/F(maximum));life.segments[index++]=ratio<1?ratio:1;threshold=metadata.nextThreshold;next=metadata.nextSubroutine;}
}
// Complete life-gauge prefix 406d0..40b0e, including countdown text/sound.
// Direct 2a80 draws use HUD coordinates; 67f0 actor translation does not apply.
export function drawEnemyLifeHud(state,bossState,draw,{entry=null,program=null,difficulty=0,spellCounter=0,chapter=0,drawNumber=null,soundSlots=[-1,-1,-1],soundDisabled=false}={}){
 if(state.v.getInt32(0x36b0,true)>=0||!bossState.active&&!state.v.getUint8(0x3ec0))return;
 const life=state.hudEnemyLife??initializeEnemyLifeHud(state),at=offset=>draw(state.vm(offset),{snap:true,space:'screen',part:'enemy-life',offset});
 at(0x2220);const fill=state.vm(0x2460),a=fill.v;a.setUint32(0xc4,(a.getUint32(0xc4,true)&~0x300)|0x400,true);a.setFloat32(0xc8,300,true);a.setFloat32(0xcc,24,true);a.setFloat32(0xd0,0,true);a.setFloat32(0xe8,F(F(F(life.smoothedFraction)*F(288))/F(14)),true);at(0x2460);
 resolveEnemyLifeSegments(state,bossState,{entry,program,difficulty,spellCounter});
 let fraction=F(life.smoothedFraction);
 for(let i=0;i<3;i++){
  const next=F(life.segments[i]);fraction=fraction<next?fraction:next;if(0>=fraction)break;
  state.bytes.set(fill.state,0x3ec8);state.anms.delete(0x3ec8);const temp=state.vm(0x3ec8),t=temp.v;t.setFloat32(0xe8,F(F(fraction*F(288))/F(14)),true);t.setUint32(0xec,(a.getUint32(0xec,true)&0xff000000)|(colors[i]&0xffffff),true);at(0x3ec8);
 }
 if(!drawNumber)throw Error('TH06nc HUD: enemy-life numeric service missing');
 const alpha=life.opacity<<24;drawNumber({format:'%d',value:String(chapter|0),text:String(chapter|0),position:[284,16,0],color:(alpha|0xffff80)>>>0});
 const seconds=bossState.remainingSeconds|0,tint=seconds>=20?0xa0d0ff:seconds>=10?0xa080ff:seconds>=5?0xe080c0:0xff4040,value=seconds>99?99:seconds;
 if(seconds<=99&&seconds<10&&(life.lastSeconds??0)!==seconds)queueSound(soundSlots,29,{disabled:soundDisabled});
 drawNumber({format:'%.2d',value:String(value),text:(value<0?'-':'')+String(Math.abs(value)).padStart(2,'0'),position:[588,16,0],color:(alpha|tint)>>>0});life.lastSeconds=seconds;
}
