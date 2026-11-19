import {createSpellMenuState} from './spell-practice-menu.mjs';
import {findSpellPractice,spellPracticeViewport} from './spell-practice-table.mjs';

// State27 tail 4ca1a..4cb5f, after resource and VM initialization. Supports
// returning directly to the previously played card as well as a cold entry.
export function finishSpellPracticeEntry(initial,{environment,table,fade,services}={}){
 if(initial.state!==27)throw Error('TH06nc: spell-menu entry state required');
 const state=createSpellMenuState(initial);
 Object.assign(state,{state:28,totalFrame:0,pulse:0,frame:0,menuFadeTicks:0,menuFadePreviousDuration:initial.menuFadeDuration??0,menuFadeDuration:0,menuFadeStartColor:0,inputDelay:30});
 if(state.resumeSpell){
  const row=findSpellPractice(table,environment.spellPracticeIndex);
  if(row){
   state.spellStage=row.stageIndex;state.spellOrder=row.order;state.spellScroll=spellPracticeViewport(table,row.stageIndex,row.order,row.order-7).start;state.spellDifficulty=row.stageIndex===6?0:row.difficulty;state.state=30;environment.configuredSpellStage=row.stageIndex;
  }else Object.assign(state,{spellStage:0,spellOrder:0,spellScroll:0,spellDifficulty:0});
  state.fastEntry=false;
 }else{
  state.spellStage=(environment.configuredSpellStage>>>0)<=6?environment.configuredSpellStage|0:0;
  state.spellOrder=0;state.spellScroll=0;state.spellDifficulty=0;state.fastEntry=true;
 }
 state.resumeSpell=false;state.leaving=false;
 for(const kind of ['stage','profile','info']){if(typeof services?.[kind]!=='function')throw Error('TH06nc: missing spell entry '+kind);services[kind](state,kind==='info'?undefined:0);}
 fade?.requestIn(0,state.fastEntry?45:30);return state;
}
