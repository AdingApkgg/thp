import {navigateTitle} from './title-navigation.mjs';
import {queueSound} from './sound-queue.mjs';
// Title replay selection, 48b45..48c48. Confirmation/cancellation and loading
// belong to the dispatcher. File rows are compacted before this helper runs.
export function navigateTitleReplayList(initial,count,keys,sound={}){
 const state={...initial};if(state.frame<40||count===0)return {state,direction:0,soundSlots:[...(sound.slots??[-1,-1,-1])]};
 const result=navigateTitle(state.selection,count,keys,sound);state.selection=result.selection;
 const press=bit=>(keys.held&bit)&&((keys.previous&bit)!==(keys.held&bit)||keys.repeat!==0);
 if(count>15&&(press(64)||press(128))){const pages=Math.ceil(count/15)*15;state.selection+=press(64)?-15:15;if(state.selection<0)state.selection+=pages;if(state.selection>=pages)state.selection-=pages;if(state.selection>=count)state.selection=count-1;queueSound(result.soundSlots,12,{disabled:sound.disabled});}
 state.replaySelection=state.selection;return {...result,state};
}
// Stage selection, 48eef..48f90. Native data always contains a stage; reject
// an empty host file instead of reproducing the native unbounded search.
export function navigateTitleReplayStage(initial,stageOffsets,keys,sound={}){
 const state={...initial};if(state.frame<40)return {state,direction:0,soundSlots:[...(sound.slots??[-1,-1,-1])]};
 const result=navigateTitle(state.selection,7,keys,sound);state.selection=result.selection;
 if(result.direction){if(!stageOffsets.some(p=>p!==null))throw Error('TH06nc replay: no recorded stage');while(stageOffsets[state.selection]===null)state.selection=(state.selection+result.direction+7)%7;}
 return {...result,state};
}
