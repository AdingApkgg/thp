import {queueSound} from './sound-queue.mjs';
// Standard/Challenge/Mouse replay stage-page entry, 48cf7..48e77. The caller
// has already selected and validated a compacted file row. SpellPr uses the
// separate direct-launch path. File decode is a synchronous caller service.
export function enterTitleReplayStage(group,initial,headerStageOffsets,{loadReplay,filename,soundSlots=[-1,-1,-1],soundDisabled=false}={}){
 const state={...initial,state:20,pulse:0,frame:0,selection:0};
 for(let i=0;i<26;i++)group.slots.get(0x13ba0+i*288).interrupt(17);
 group.slots.get(0x13f00+(initial.selection%15)*288).interrupt(16);
 queueSound(soundSlots,10,{disabled:soundDisabled});const decoded=loadReplay(filename,true);
 while(state.selection<7&&headerStageOffsets[state.selection]===null)state.selection++;
 return {state,decoded};
}
