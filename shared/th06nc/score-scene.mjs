import {ResultState,advanceResultCommon} from './result-state.mjs';
import {TitleInput} from './title-navigation.mjs';
import {NativeFade} from './fade.mjs';
import {createAsciiTextState} from './ascii-text.mjs';
import {advanceScoreMenu} from './score-menu-update.mjs';
import {advanceScoreRank} from './score-rank-update.mjs';
import {advanceScoreSpell} from './score-spell-update.mjs';
import {advanceScoreSecret} from './score-secret-unlock.mjs';
import {advanceResultExit} from './result-exit.mjs';
import {drawResultReplay} from './result-replay-draw.mjs';

export class ScoreScene {
 constructor(bank,{tables,spellRecords,spellTable,cleared,localization={},publishText,fade=new NativeFade()}={}){
  this.state=new ResultState(bank);this.ascii=createAsciiTextState(bank);this.input=new TitleInput();this.fade=fade;this.sounds=[-1,-1,-1];this.services={tables,spellRecords,spellTable,cleared,localization,publishText};this.handoff=null;
 }
 tick(mask=0,{keyboardMask=0,controllerMask=0}={}){
  if(this.handoff)return this.handoff;this.fade.tick();const kind=this.state.v.getInt32(0x9e94,true),keys={...this.services,...this.input.sample(mask),soundSlots:this.sounds,fade:this.fade};
  if(kind<=1)advanceScoreMenu(this.state,keys);
  else if(kind===2){const event=advanceResultExit(this.state,this.fade);if(event){this.handoff=event;return event;}}
  else if(kind===8)advanceScoreSpell(this.state,keys);
  else advanceScoreRank(this.state,{...keys,processSecretUnlock:state=>advanceScoreSecret(state,{...keys,keyboardMask,controllerMask})});
  advanceResultCommon(this.state,kind);return null;
 }
 draw(draw,setupCamera){drawResultReplay(this.state,draw,{...this.services,ascii:this.ascii,setupCamera});}
 report(){const v=this.state.v;return {state:v.getInt32(0x9e94,true),viewMode:v.getInt32(0x9e9c,true),clock:v.getInt32(0x4450,true),selection:v.getInt32(0x9e7c,true),difficulty:v.getInt32(0xa8,true),profile:v.getInt32(4,true),spellPage:v.getInt32(0x18,true),spellCount:v.getInt32(0xa4,true),dirty:Boolean(v.getUint8(0x9e99)),keyboardProgress:v.getInt32(0x4430,true),controllerProgress:v.getInt32(0x4448,true),cleared:[...this.services.cleared],handoff:this.handoff,fade:{mode:this.fade.mode,alpha:this.fade.alpha}};}
}
