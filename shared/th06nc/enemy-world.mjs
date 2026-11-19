import {clearOrdinaryEnemies} from './enemy-clear.mjs';
import {EnemyPool} from './enemy-pool.mjs';
import {EclTimeline} from './ecl-timeline.mjs';
import {tickOrdinaryEnemy} from './enemy-ordinary.mjs';
import {drawEnemyAnimations} from './enemy-draw.mjs';
import {createBossState,setBossRegistration} from './boss-state.mjs';
import {createSpellState,beginSpell,endSpell} from './spell-state.mjs';
import {spawnSpellPracticeEnemy} from './spell-practice-spawn.mjs';
// Ordinary world manager ordering, 373b0: timeline, occupied slots, clock.
// Real player, bullet, item, effect and message managers must supply services.
export class EnemyWorld {
 constructor(program,{anmBank,environment={},openMessage=null,...services}={}){
  this.environment=environment;this.bossSlots=[];this.bossState=createBossState();this.spellState=createSpellState(services.spellBackground);
  this.spellPracticeTable=services.spellPracticeTable??null;
  this.chapter=0;
  this.services={...services,spawnEnemy:request=>this.pool.spawn(request),clearEnemies:()=>clearOrdinaryEnemies(this.pool),signalBackground:services.signalBackground??(()=>{if(services.spellBackground)services.spellBackground.v.setUint8(0x68,1);else environment.backgroundSignal=true;}),soundSlots:services.soundSlots??[-1,-1,-1],bossState:this.bossState,beginSpell:(enemy,args)=>beginSpell({v:new DataView(enemy.buffer,enemy.byteOffset,enemy.byteLength)},args,{environment,spellState:this.spellState,localization:services.localization,soundSlots:this.services.soundSlots,soundDisabled:services.soundDisabled,cancelBullets:services.cancelBullets,publishSpellIntro:services.publishSpellIntro}),endSpell:()=>endSpell({environment,spellState:this.spellState,bossState:this.bossState,cancelBullets:services.cancelBullets}),registerBoss:(enemy,index)=>setBossRegistration(enemy,index,{bossSlots:this.bossSlots,bossState:this.bossState,environment}),advanceStageChapter:chapter=>{this.timeline.messageClock=(this.timeline.messageClock+1800)|0;this.chapter=chapter;}};
  this.pool=new EnemyPool(program,{anmBank,environment,...this.services});
  this.timeline=new EclTimeline(program.timelines[0],{environment,bossSlots:this.bossSlots,spawn:args=>this.pool.spawn(args),openMessage});
  this.activeCount=0;this.previousFrame=0;
 }
 tick(){
  let timeline;
  if(this.environment.spellPractice){const entry=spawnSpellPracticeEnemy(this.pool,this.spellPracticeTable);timeline={blocked:false,processed:0,spellPractice:true,spawned:entry?.slot??null};}
  else timeline=this.timeline.runDue();this.activeCount=0;
  for(let slot=0;slot<256;slot++){
   const entry=this.pool.entries[slot];if(!entry||!(entry.v.getUint8(0xbc)&128))continue;
   this.activeCount++;tickOrdinaryEnemy(entry,{...this.services,environment:this.environment});
  }
  this.previousFrame=this.timeline.frame;this.timeline.frame=(this.timeline.frame+1)|0;
  return {timeline,activeCount:this.activeCount,frame:this.timeline.frame};
 }
 draw(draw,options){for(const entry of this.pool.entries)if(entry)drawEnemyAnimations(entry,draw,options);}
}
