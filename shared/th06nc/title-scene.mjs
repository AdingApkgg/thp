import {titleLaunchAchievement} from './achievement-checks.mjs';
import {updateTitleOptions} from './title-options-update.mjs';
import {updateTitleDisplayOptions} from './title-display-options.mjs';
import {updateTitleKeyOptions} from './title-key-options.mjs';
import {advanceTitleOptionsEntry} from './title-options-entry.mjs';
import {titleMenuHandoff} from './title-menu-handoff.mjs';
import {advanceSelectionReturn,warmTitleMain,finishWarmTitleMain,titlePromptReady} from './title-selection-return.mjs';
import {updatePracticeStages} from './title-practice-update.mjs';
import {practiceStageDrawPlan} from './title-practice-draw.mjs';
import {enqueueAsciiText} from './ascii-text.mjs';
import {TitleAnimations} from './title-animations.mjs';
import {TitleBackdrop} from './title-backdrop.mjs';
import {TitleInput} from './title-navigation.mjs';
import {updateTitleMain} from './title-main-update.mjs';
import {advanceTitleOwnerCommon} from './title-owner-advance.mjs';
import {selectionLoadPlan,initializeSelectionAnimations,finishSelectionEntry} from './title-selection-layout.mjs';
import {updateTitleDifficulty} from './title-difficulty-update.mjs';
import {updateTitleCharacter} from './title-character-update.mjs';
import {updateTitleShot} from './title-shot-update.mjs';
import {updateTitleMode} from './title-mode-update.mjs';
import {updateTitleLaunch} from './title-launch-update.mjs';
import {drawTitleBackdropBase} from './title-backdrop-draw.mjs';
import {drawStableTitleMain} from './title-main-draw.mjs';
import {NativeFade} from './fade.mjs';
import {initializeTitleReplayAnimations} from './title-replay-layout.mjs';
import {navigateTitleReplayList,navigateTitleReplayStage} from './title-replay-navigation.mjs';
import {enterTitleReplayStage} from './title-replay-stage-entry.mjs';
import {prepareTitleReplayLaunch} from './title-replay-launch.mjs';
import {drawTitleReplay} from './title-replay-draw.mjs';
import {createAsciiTextState} from './ascii-text.mjs';
import {queueSound} from './sound-queue.mjs';
import {asciiFontAssets} from './ascii-layout.mjs';
import {TitleReplayBackground} from './title-replay-background.mjs';
import {SpellPracticePresentation} from './spell-practice-presentation.mjs';

// Main-owner scene adapter. Boot/splash and the other menu destination owners
// remain separate work; this adapter preserves the already verified main flow.
export class TitleScene {
 constructor(resources,{coldStartup=false,extraAvailable=false,extraUnlockedShots=[[false,false],[false,false]],soundDisabled=true,musicState=null,replayServices=null,spellServices=null,cleared=new Uint8Array(96).fill(1),practiceScores=new Uint8Array(2304),configuredPracticeStage=0,configuredCharacter=0,configuredShot=0,optionsServices=null}={}){
  this.optionsServices=optionsServices;this.spellServices=spellServices;this.spellPresentation=null;
  this.cleared=cleared;this.practiceScores=practiceScores;this.replayServices=replayServices;this.replayRecords=[];this.replayDecoded=null;this.replayEnvironment={};this.ascii=null;this.replayBackground=null;
  this.extraUnlockedShots=extraUnlockedShots;this.soundDisabled=soundDisabled;
  this.musicState=musicState;
  this.resources=resources;this.extraAvailable=extraAvailable;this.group=new TitleAnimations(resources);this.backdrop=new TitleBackdrop(this.group);this.input=new TitleInput();this.fade=new NativeFade();this.fades=new Int32Array(10);this.sounds=[-1,-1,-1];this.background=null;this.handoff=null;this.effects=[];
  this.state={state:3,selection:0,frame:0,pulse:0,totalFrame:0,inputCooldown:0,entryHold:false,previousGroupState:3,menuColor:0x80ffffff,practice:0,spell:0,difficulty:1,configuredDifficulty:optionsServices?.config?.[21]??1,configuredCharacter,configuredShot,configuredMode:optionsServices?.config?.[23]??0,configuredPracticeStage};
  if(coldStartup){
   this.state=warmTitleMain(this.group,{...this.state,startupOverlay:true,backgroundEnabled:true},this.backdrop);
   this.fade.requestIn(0,200);
   return;
  }
  for(const i of [0,1,2,50,3,4,5,6,7,8])this.group.slots.get(0x9640+i*288).interrupt(2);for(const vm of this.backdrop.vms.slice(0,2))vm.interrupt(1);this.backdrop.request(1);
 }
 tick(mask){
  if(this.handoff)return this.handoff;
  const config=this.optionsServices?.config;
  if(config){
   this.state.configuredDifficulty=config[21];
   this.state.configuredMode=config[23];
  }
  const previousDifficulty=this.state.configuredDifficulty;
  const previousFrame=this.state.frame;
  const previousState=this.state.state;
  if([27,28,29,30,31].includes(previousState)&&!this.spellServices)return {kind:'unimplementedMenu',state:previousState};
  if([4,6,7].includes(previousState)&&!this.optionsServices)return {kind:'unimplementedMenu',state:previousState};
  if([15,16,17,18,19,20,26].includes(previousState)&&!this.replayServices)return {kind:'unimplementedMenu',state:previousState};
  if(![0,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31].includes(previousState))return {kind:'unimplementedMenu',state:previousState};
  this.fade.tick();
  if(previousState===25&&this.fade.mode===2){this.handoff={kind:'startGame',achievement:titleLaunchAchievement(this.state.launchFrom),stage:(this.state.stageIndex??0)+1,difficulty:this.state.difficulty,character:this.state.configuredCharacter,shot:this.state.configuredShot,mode:this.state.configuredMode,practice:this.state.practice};return this.handoff;}
  if(previousState===26&&this.fade.mode===2){this.handoff={kind:'startReplay',environment:{...this.replayEnvironment},decoded:this.replayDecoded};return this.handoff;}
  if(previousState===19&&this.state.frame===30){this.handoff={kind:'returnTitle',selection:4};return this.handoff;}
  if([5,12,21,23].includes(previousState)){const event=titleMenuHandoff(previousState,this.state.frame,this.fade);if(event){this.handoff=event;return event;}}
  const keys=this.input.sample(mask),sound={disabled:this.soundDisabled,slots:this.sounds};let result;
  if(previousState===10)result={state:advanceSelectionReturn(this.state)};
  else if(previousState===0){this.group=new TitleAnimations(this.resources);this.backdrop=new TitleBackdrop(this.group);this.background=null;this.ascii=null;this.replayBackground=null;this.fades.fill(0);this.input=new TitleInput();result={state:warmTitleMain(this.group,{...this.state,backgroundEnabled:true},this.backdrop)};this.fade.requestIn(0,30);}
  else if(previousState===2&&!titlePromptReady(this.state,keys))result={state:{...this.state}};
  else if(previousState===2){this.fades.fill(0);result=updateTitleMain(this.group,finishWarmTitleMain(this.group,this.state,{backdrop:this.backdrop,fade:this.fade}),keys,{extraAvailable:this.extraAvailable,fades:this.fades,sound});}
  else if(previousState===3)result=updateTitleMain(this.group,this.state,keys,{extraAvailable:this.extraAvailable,fades:this.fades,sound});
  else if(previousState===4)result=updateTitleOptions(this.group,this.state,keys,{...this.optionsServices,sound});
  else if(previousState===7)result=updateTitleDisplayOptions(this.group,this.state,keys,{...this.optionsServices,sound});
  else if(previousState===6)result=updateTitleKeyOptions(this.group,this.state,keys,{...this.optionsServices,sound,deviceKind:this.optionsServices.deviceKind(),buttons:this.optionsServices.buttons(),loadButtonIcons:ref=>this.group.bank.load(this.resources.get(ref.file),ref.base,{slot:ref.slot})});
  else if(previousState===8){const plan=selectionLoadPlan(this.state);if(plan){initializeSelectionAnimations(this.group,this.resources);this.background=plan.background.split('/').at(-1).replace(/\.png$/,'');result=finishSelectionEntry(this.group,this.state);}}
  else if(previousState===9)result=updateTitleDifficulty(this.group,this.state,keys,{sound,configuredCharacter:this.state.configuredCharacter,extraUnlockedCharacters:this.extraUnlockedShots.map(row=>row.some(Boolean))});
  else if(previousState===11)result=updateTitleCharacter(this.group,this.state,keys,{extraUnlockedShots:this.extraUnlockedShots});
  else if(previousState===13)result=updateTitleShot(this.group,this.state,keys,{sound,extraUnlockedShots:this.extraUnlockedShots,configuredMode:Boolean(this.state.configuredMode)});
  else if(previousState===14)result=updateTitleMode(this.group,this.state,keys,{sound,cleared:this.cleared});
  else if(previousState===22)result=updatePracticeStages(this.group,this.state,keys,{sound,cleared:this.cleared});
  else if([5,12,21,23].includes(previousState))result={state:{...this.state}};
  else if(previousState===24)result=updateTitleLaunch(this.group,this.state,keys,{musicActive:Boolean(this.musicState?.playing)});
  else if(previousState===27){
   const plan=selectionLoadPlan(this.state);
   if(plan){const environment=this.spellServices.environment;Object.assign(environment,{character:this.state.configuredCharacter,shot:this.state.configuredShot});this.spellPresentation=new SpellPracticePresentation(this.group,this.resources,this.spellServices);this.background='select00e';result={state:this.spellPresentation.enter({...this.state,backgroundEnabled:false},this.fade)};}
  }
  else if([28,29,30,31].includes(previousState)){
   result=this.spellPresentation.tick(this.state,keys,{fade:this.fade,soundSlots:this.sounds,soundDisabled:this.soundDisabled,music:this.musicState});
   const environment=this.spellServices.environment;Object.assign(result.state,{configuredCharacter:environment.character,configuredShot:environment.shot});
   if(result.launchReady){this.state=result.state;this.handoff={kind:'startSpellPractice',environment:{...environment}};return this.handoff;}
  }
  else if([15,16,17,18,20].includes(previousState))result=this.tickReplay(keys,sound);
  if(result?.state.state===22&&!this.ascii){for(const ref of asciiFontAssets)this.group.bank.load(this.resources.get(ref.file),ref.base,{slot:ref.slot});this.ascii=createAsciiTextState(this.group.bank);}
  this.effects=result?.effects??[];if(result){this.state=result.state;this.fades=result.fades??this.fades;this.sounds=result.soundSlots??this.sounds;}
  for(const effect of this.effects){if(effect.kind==='fade')this.fade.requestOut(effect.mode,effect.frames);else if(effect.kind==='entryFade')this.fade.requestIn(0,effect.frames);}
  if(config){
   if(this.state.configuredDifficulty!==previousDifficulty)config[21]=this.state.configuredDifficulty;
   const modeEdited=previousState===14&&previousFrame>=15&&
    [256,512].some(bit=>(keys.held&bit)!==0&&(keys.held&bit)!==(keys.previous&bit));
   if(modeEdited)new DataView(config.buffer,config.byteOffset,config.byteLength).setUint16(23,this.state.configuredMode,true);
   this.state.configuredDifficulty=config[21];
   this.state.configuredMode=config[23];
  }
  this.state=advanceTitleOptionsEntry(this.group,this.state,previousState);this.state=advanceTitleOwnerCommon(this.group,this.state,this.backdrop,{previousState});if(this.replayBackground&&[17,18,19,20,26].includes(this.state.state))this.replayBackground.tick();return null;
 }
 tickReplay(keys,sound){
  const state={...this.state},edge=bit=>(keys.held&bit)&&((keys.previous&bit)!==(keys.held&bit)),interrupt=id=>{for(const [p,vm]of this.group.slots)if(p>=0x9640&&p<0x15900)vm.interrupt(id);},read=path=>this.replayServices.readReplay(path);
  if(!this.replayServices)return {state:{...state,state:state.state},effects:[]};
  if(state.state===15){state.state=16;return {state};}
  if(state.state===16){this.replayRecords=this.replayServices.records();state.state=17;return {state};}
  if(state.state===17){if(state.frame<50)return {state};for(const slot of [21,22,23,24,25,26,27,28,29])this.group.bank.unload(slot);initializeTitleReplayAnimations(this.group,this.resources);for(const ref of asciiFontAssets)this.group.bank.load(this.resources.get(ref.file),ref.base,{slot:ref.slot});this.ascii=createAsciiTextState(this.group.bank);this.replayBackground=new TitleReplayBackground(this.group.bank,this.resources.get('select00d.anm'));this.background=null;Object.assign(state,{state:18,pulse:0,selection:0,replaySelection:0,backgroundEnabled:false,menuFadePreviousDuration:state.menuFadeDuration??0,menuFadeDuration:0,menuFadeTicks:0,menuFadeStartColor:0});interrupt(15);this.fade.requestIn(0,30);return {state};}
  if(state.frame<40)return {state};
  if(state.state===18){const nav=navigateTitleReplayList(state,this.replayRecords.length,keys,sound);Object.assign(state,nav.state);this.sounds=nav.soundSlots;
   if(this.replayRecords.length&&edge(256)){const row=this.replayRecords[state.selection],header=row.header;if(header[6]===3){this.replayDecoded=read(row.path);const first=this.replayDecoded.stageOffsets.findIndex(p=>p!==null),launch=prepareTitleReplayLaunch(state,this.replayDecoded,first,{environment:this.replayEnvironment,filename:row.path,spellRecords:this.replayServices.spellRecords??[],fade:this.fade,soundSlots:this.sounds,soundDisabled:this.soundDisabled});Object.assign(state,launch.state);if(!launch.accepted)queueSound(this.sounds,11,{disabled:this.soundDisabled});}
    else{const offsets=Array.from({length:7},(_,i)=>new DataView(header.buffer,header.byteOffset,header.byteLength).getBigUint64(64+i*8,true)===0n?null:1),entry=enterTitleReplayStage(this.group,state,offsets,{filename:row.path,loadReplay:read,soundSlots:this.sounds,soundDisabled:this.soundDisabled});Object.assign(state,entry.state);this.replayDecoded=entry.decoded;}}
   if(edge(512)){Object.assign(state,{state:19,frame:0,selection:4});interrupt(4);this.replayBackground.close();queueSound(this.sounds,11,{disabled:this.soundDisabled});this.fade.requestOut(0,30);}
  }else{const nav=navigateTitleReplayStage(state,this.replayDecoded.stageOffsets,keys,sound);Object.assign(state,nav.state);this.sounds=nav.soundSlots;
   if(edge(256)&&this.replayDecoded.stageOffsets[state.selection]!==null){const launch=prepareTitleReplayLaunch(state,this.replayDecoded,state.selection,{environment:this.replayEnvironment,filename:this.replayRecords[state.replaySelection].path,fade:this.fade,soundSlots:this.sounds,soundDisabled:this.soundDisabled});return {state:launch.state,soundSlots:this.sounds};}
   if(edge(512)){this.replayDecoded=null;Object.assign(state,{state:18,frame:0,pulse:0,selection:state.replaySelection});interrupt(15);queueSound(this.sounds,11,{disabled:this.soundDisabled});}
  }return {state,soundSlots:this.sounds};
 }
 draw(drawVm,drawBackground,drawFade,options={}){
  if(this.background)drawBackground(this.background);
  if(this.replayBackground)this.replayBackground.draw(drawVm);
  if(this.state.backgroundEnabled!==false){drawTitleBackdropBase(this.group,drawVm);drawVm(this.group.slots.get(0x15990),{snap:true});}
  if(this.ascii)for(const request of practiceStageDrawPlan(this.state,{cleared:this.cleared,practiceScores:this.practiceScores}))enqueueAsciiText(this.ascii,request);
  drawStableTitleMain(this.group,drawVm,this.state);
  if(this.spellPresentation)this.spellPresentation.draw(this.state,drawVm,options);
  if(this.ascii&&[18,19,20,26].includes(this.state.state))drawTitleReplay(this.group,drawVm,{state:this.state,records:this.replayRecords,decoded:this.replayDecoded,ascii:this.ascii});
  if(this.state.backgroundEnabled!==false&&this.backdrop.vms[1].v.getUint8(0xef))drawVm(this.backdrop.vms[1],{snap:true});
  if(this.replayBackground)this.replayBackground.drawFront(drawVm);
  if(this.fade.mode)drawFade(((this.fade.alpha&255)<<24)|this.fade.color);
 }
}
