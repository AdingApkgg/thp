import {spellPracticeStageComplete} from './spell-practice-table.mjs';

// Title initialization 55a50..55c3e: consume the launch snapshot before
// clearing the title owner, then publish the two deferred notice requests.
export function prepareSpellPracticeReturn(environment,{table,records,startup=false}={}){
 const e=environment,profile=(e.character&255)*2+(e.shot&255),resumeSpell=!startup&&Boolean(e.resumeSpell);
 const state={resumeSpell,noticePending:false,noticeRecord:null,noticeProfile:0,completePending:false,completeStage:0,completeProfile:0};
 if(e.titleLaunchPending){
  e.titleLaunchPending=false;
  if(resumeSpell&&(e.lastSpellProfile&255)===profile&&(e.lastSpellId&255)===(e.spellPracticeIndex&255)){
   const row=table.find(row=>row.id===(e.lastSpellId&255));
   if(row&&!e.spellWasCaptured&&row.id<134&&row.difficulty<5&&(e.lastSpellProfile&255)<=3&&records.get(row.id)?.practiceCaptures[row.difficulty*4+(e.lastSpellProfile&255)]){
    Object.assign(state,{noticePending:true,noticeRecord:row,noticeProfile:profile&255});
    if(!e.spellStageWasComplete&&spellPracticeStageComplete(table,records,row.stageIndex,e.character,e.shot))Object.assign(state,{completePending:true,completeStage:row.stageIndex,completeProfile:profile&255});
   }
  }
 }
 if(resumeSpell)e.resumeSpell=false;
 return state;
}
