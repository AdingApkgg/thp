import {initializeResultEntryFade} from './result-entry-fade.mjs';
import {ResultState,advanceResultCommon} from './result-state.mjs';
import {createDefaultScoreTables} from './score-tables.mjs';
import {qualifyResultScore} from './score-qualify.mjs';
import {advanceScoreNameInput} from './score-name-input.mjs';
import {TitleInput} from './title-navigation.mjs';
import {NativeFade} from './fade.mjs';
import {createAsciiTextState} from './ascii-text.mjs';
import {drawResultName} from './result-name-draw.mjs';
import {advanceResultSummary} from './result-summary.mjs';
import {drawResultSummary} from './result-summary-draw.mjs';
import {advanceResultReplayGate} from './result-replay-gate.mjs';
import {advanceResultExit} from './result-exit.mjs';
import {drawResultReplay} from './result-replay-draw.mjs';
import {initializeResultReplayList} from './result-replay-list-init.mjs';
import {advanceResultReplayList,advanceResultReplayOverwrite} from './result-replay-list.mjs';
import {advanceReplayNameInput} from './result-replay-name-input.mjs';
export function resultProfileName(profile,mode,localization={}){
 const player=['EXE_REIMU_A_NAME','EXE_REIMU_B_NAME','EXE_MARISA_A_NAME','EXE_MARISA_B_NAME'][profile],style=['EXE_RESULT_MODE_NORMAL_NAME','EXE_RESULT_MODE_CHALLENGE_NAME','EXE_RESULT_MODE_MOUSE_NAME'][mode];if(!player||!style)throw Error('TH06nc result: invalid profile/mode label');return (localization[player]??player)+' / '+(localization[style]??style);
}
// State-9 entry label/body, 707cc..70bab. Qualification follows this block.
export function initializeResultNamePage(state,environment,{localization={},publishText=null}={}){
 const {v}=state,character=environment.character&255,difficulty=environment.difficulty|0,mode=Number(Boolean(environment.lifeProtection));v.setInt32(4,character,true);v.setInt32(0xa8,difficulty,true);v.setInt32(0xac,mode,true);
 for(let i=0;i<38;i++)v.setInt16(0xb0+i*288+0x8a,difficulty+3,true);
 for(let side=0;side<2;side++){const p=0x2b70+side*288;v.setUint32(p+0xc4,(v.getUint32(p+0xc4,true)&~0x400)|0x300,true);publishText?.(state.vm(p),{text:resultProfileName(character*2+side,mode,localization),colors:[0xffffff,0,0x10101,0x40202]});if((environment.shot&255)!==side)v.setUint32(p+0xec,0x80ffffff,true);}
}
// Ordinary name registration until its authentic state-15 handoff. The summary
// and replay-save states remain the responsibility of the result dispatcher.
export class ResultNameScene {
 constructor(anmBank,{environment,localization={},publishText=null,previousName='',tables=createDefaultScoreTables(),fade=new NativeFade(),achievement=null,saveName=null,replayServices=null,standalone=false}={}){
  this.state=new ResultState(anmBank);this.state.v.setInt32(0x9e94,standalone?12:9,true);this.state.v.setInt32(0x9e9c,standalone?12:9,true);this.state.bytes[0x9e9a]=Number(Boolean(standalone));this.environment=environment;this.localization=localization;this.publishText=publishText;this.previousName=previousName;this.tables=tables;this.fade=fade;this.input=new TitleInput();this.sounds=[-1,-1,-1];this.achievement=achievement;this.saveName=saveName;this.replayServices=replayServices;this.ascii=createAsciiTextState(anmBank);this.qualification=null;this.handoff=null;initializeResultEntryFade(fade,{state:standalone?12:9,standalone});
 }
 tick(mask=0){
  if(this.handoff)return this.handoff;this.fade.tick();const state=this.state,v=state.v,previous=v.getInt32(0x9e94,true),keys=this.input.sample(mask);
  if(v.getInt32(0x4450,true)===0){initializeResultNamePage(state,this.environment,{localization:this.localization,publishText:this.publishText});const table=this.tables.get(`${v.getInt32(0xac,true)}/${v.getInt32(0xa8,true)}/${(this.environment.character&255)*2+(this.environment.shot&255)}`);if(!table)throw Error('TH06nc result: missing selected rank table');this.qualification=qualifyResultScore(state,table,{...this.environment,previousName:this.previousName});}
  if(v.getInt32(0x9e94,true)===9)advanceScoreNameInput(state,{...keys,soundSlots:this.sounds,achievement:this.achievement,saveName:this.saveName});advanceResultCommon(state,previous);
  if(v.getInt32(0x9e94,true)===15)this.handoff={kind:'resultSummary',rank:this.qualification.rank,qualifies:this.qualification.qualifies};return this.handoff;
 }
 tickSummary(mask=0){
  const state=this.state,v=state.v,previous=v.getInt32(0x9e94,true);if(this.handoff?.kind==='replaySelection')return this.handoff;
  this.fade.tick();advanceResultSummary(state,this.input.sample(mask));advanceResultCommon(state,previous);
  if(v.getInt32(0x9e94,true)===10){this.handoff={kind:'replaySelection'};return this.handoff;}return null;
 }
 tickReplay(mask=0){
  if(['returnTitle','replayListRequested','replayRecordingUnavailable'].includes(this.handoff?.kind))return this.handoff;
  this.fade.tick();const previous=this.state.v.getInt32(0x9e94,true),keys=this.input.sample(mask);
  if(previous===2){const event=advanceResultExit(this.state,this.fade);if(event){this.handoff=event;return event;}}
  else if(previous===12)advanceResultReplayList(this.state,{...this.replayServices,...keys,soundSlots:this.sounds,date:this.replayServices?.localDate?.()??this.replayServices?.date??'00/00/00'});
  else if(previous===14)advanceResultReplayOverwrite(this.state,{...this.replayServices,...keys,soundSlots:this.sounds});
  else if(previous===13){const event=advanceReplayNameInput(this.state,{...this.replayServices,...keys,soundSlots:this.sounds,saveName:this.saveName});if(event&&!this.replayServices?.recordingAvailable)this.handoff={kind:'replayRecordingUnavailable'};}
  else advanceResultReplayGate(this.state,{...keys,continuesUsed:this.environment.continuesUsed??0,soundSlots:this.sounds,openReplayList:()=>{if(this.replayServices)initializeResultReplayList(this.state,{...this.replayServices,soundSlots:this.sounds});else this.handoff={kind:'replayListRequested'};}});
  advanceResultCommon(this.state,previous);return ['replayListRequested','replayRecordingUnavailable'].includes(this.handoff?.kind)?this.handoff:null;
 }
 draw(draw,setupCamera){const state=this.state.v.getInt32(0x9e94,true);if(state===9)drawResultName(this.state,draw,{ascii:this.ascii,tables:this.tables,shot:this.environment.shot,setupCamera});else if(state===15||state===16)drawResultSummary(this.state,draw,{ascii:this.ascii,tables:this.tables,environment:this.environment,setupCamera});else drawResultReplay(this.state,draw,{ascii:this.ascii,tables:this.tables,environment:this.environment,setupCamera});}
 report(){const {v,bytes}=this.state;return {state:v.getInt32(0x9e94,true),clock:v.getInt32(0x4450,true),selection:v.getInt32(0,true),replaySlot:v.getInt32(0x4438,true),replayName:String.fromCharCode(...bytes.subarray(0x9e88,0x9e90)),length:v.getInt32(0x9e7c,true),name:String.fromCharCode(...bytes.subarray(0x9e70,0x9e78)),rank:this.qualification?.rank??null,qualifies:this.qualification?.qualifies??null,handoff:this.handoff,fade:{mode:this.fade.mode,alpha:this.fade.alpha}};}
}
