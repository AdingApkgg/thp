import {runUpdateChain} from './task-update-chain.mjs';
import {replayDialogueTaskResult} from './replay-playback.mjs';
// A gameplay update includes input sampling and all world/message updates that
// precede replay priority 16. Restart repeats that entire callback. The caller
// retains scene transitions and the remaining application's task ordering.
export function runReplayFrame(playback,{update,active=()=>true,message=()=>null,consumeSounds=()=>{}}){
 let updates=0;const tail={next:null,update:()=>{if(!active())return 1;const v=message();return replayDialogueTaskResult(playback.v.getInt32(0x30,true),{active:true,messageField:v?.getInt32(0x36b0,true)??-1,indicator:Boolean(v?.getUint8(0x3900))});}},head={next:tail,update:()=>{updates++;update();return 1;}};
 runUpdateChain(head,{status:{value:0},consumeSounds});return updates;
}
