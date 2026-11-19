import {AnmBank} from './anm-bank.mjs';
import {rebindAnm} from './anm-rebind.mjs';
import {initializeSpellMenuAnimations} from './spell-practice-layout.mjs';
import {spellInfoTextAsset} from './spell-practice-info-text.mjs';
import {refreshSpellCharacter,refreshSpellProfile} from './spell-practice-profile.mjs';
import {refreshSpellPracticeStageInfo} from './spell-practice-stage-info.mjs';
import {refreshSpellPracticeCardInfo} from './spell-practice-card-info.mjs';
import {finishSpellPracticeEntry} from './spell-practice-entry.mjs';
import {updateSpellPracticeMenu} from './spell-practice-menu.mjs';
import {drawSpellPractice} from './spell-practice-draw.mjs';
import {drawSpellProfilePreview,drawSpellProfileLabels} from './spell-practice-profile-draw.mjs';

export const spellDifficultyAsset=Object.freeze({archive:'th06TL.dat',file:'difficulty.anm',slot:66,base:0x792});

// Connect the verified spell-menu components to one retained title ANM bank.
// Resource transport, localization/font painting and the game handoff are hosts.
export class SpellPracticePresentation {
 constructor(group,resources,{table,records,environment,localization,publishText}){
  Object.assign(this,{group,resources,table,records,environment,localization,publishText});
  this.services={
   stage:(state,direction)=>refreshSpellCharacter(group,state,environment.character,direction),
   profile:(state,direction)=>refreshSpellProfile(group,state,environment.character,environment.shot,direction),
   info:state=>(state.state===28?refreshSpellPracticeStageInfo:refreshSpellPracticeCardInfo)(group,state,{table,records,character:environment.character,shot:environment.shot,localization,publishText}),
  };
 }
 enter(initial,fade){
  initializeSpellMenuAnimations(this.group,this.resources);
  for(const ref of [spellInfoTextAsset,spellDifficultyAsset]){
   const resource=this.resources.get(ref.file);if(!resource)throw Error('TH06nc: spell presentation resource missing '+ref.file);
   this.group.bank.load(resource,ref.base,{slot:ref.slot});
  }
  // 55840's direct-sprite VM initialization, shared with the replay menu.
  const empty=new AnmBank(),scratch=rebindAnm(empty,0,new Uint8Array(288),{resolveSprite:id=>this.group.bank.sprites.get(id)});
  scratch.v.setUint16(0x108,0xf0f,true);scratch.v.setInt32(0xb4,-1,true);scratch.bindSprite(0x792);scratch.v.setUint32(0xc4,(scratch.v.getUint32(0xc4,true)&~0x300)|0x401,true);this.group.slots.set(0x16050,scratch);
  return finishSpellPracticeEntry(initial,{environment:this.environment,table:this.table,fade,services:this.services});
 }
 tick(state,keys,options){return updateSpellPracticeMenu(state,keys,{...options,table:this.table,records:this.records,environment:this.environment,services:this.services});}
 draw(state,draw,options={}){
  if(![28,29,30,31].includes(state.state))return;
  const services={...options,table:this.table,records:this.records,character:this.environment.character,shot:this.environment.shot};
  drawSpellProfilePreview(this.group,state,draw,services);
  if(state.state===28){drawSpellPractice(this.group,state,draw,services);drawSpellProfileLabels(this.group,state,draw,services);}
  else{drawSpellProfileLabels(this.group,state,draw,services);drawSpellPractice(this.group,state,draw,services);}
 }
}
