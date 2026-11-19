import {ResultState} from './result-state.mjs';
// Practice power correction after one-based stage publication, 3afe5..3b00b.
export function practiceStartingPower(stage,power){return stage===1?power:stage===2?64:128;}
// Result state 17, 6e43e..6e4db. It does not advance the common result ANMs.
export function advancePracticeResult(state,fade){
 if(!state.bytes[0x9e98]){state.bytes[0x9e98]=1;if(fade&&fade.mode!==2)fade.requestOut(0,30);}
 return fade?.mode===2?0:1;
}

export class PracticeResultScene {
 constructor(bank,{fade}){this.state=new ResultState(bank);this.fade=fade;this.state.v.setInt32(0x9e94,17,true);this.state.v.setInt32(0x9e9c,17,true);this.state.bytes[0x9e99]=1;}
 tick(){return advancePracticeResult(this.state,this.fade);}
 report(){return {state:17,clock:this.state.v.getInt32(0x4450,true),fade:{mode:this.fade.mode,alpha:this.fade.alpha}};}
}
