import {practiceStageCount} from './title-practice-entry.mjs';
// Practice list before stable title ANMs, 54ca8..54f3f. Scores are PSCR u64.
export function practiceStageDrawPlan(state,{cleared,practiceScores}){
 if(state.state!==22&&(![24,25].includes(state.state)||state.launchFrom!==22))return [];
 const alpha=state.state===22&&!state.spell&&state.frame<30?Math.trunc(Math.imul(state.frame,255)/30):255;
 const selected=state.state===22?state.selection:state.configuredPracticeStage,requests=[],v=new DataView(practiceScores.buffer,practiceScores.byteOffset,practiceScores.byteLength);
 const t=state.pulse%72,pulse=t<30?128+Math.trunc(t*127/30):t<42?255:128+Math.trunc((72-t)*127/30);
 for(let stage=0;stage<practiceStageCount(cleared,state);stage++){
  const active=stage===selected,a=state.state===22?pulse:255;
  const color=active?((Math.trunc((a&255)*alpha/255)<<24)|0xc0f0f0)>>>0:((alpha<<23)|0x80c0c0)>>>0;
  const index=(((state.configuredCharacter*2+state.configuredShot)*6+stage)*4+state.difficulty)*24+12;
  requests.push({text:`STAGE ${stage+1}  ${String(v.getBigUint64(index,true)).padStart(9,'0')}`,position:[560,15+stage*24,0],color});
 }
 return requests;
}
