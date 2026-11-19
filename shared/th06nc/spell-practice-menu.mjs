import {spellPracticeViewport,spellPracticeOrderUnlocked,spellPracticeStageComplete} from './spell-practice-table.mjs';
import {queueSound} from './sound-queue.mjs';

export const spellMenuFields=Object.freeze({stageTransition:0x168ec,orderTransition:0x168f4,difficultyTransition:0x168fc,profileTransition:0x16900,noticeClock:0x16914,completeClock:0x16924});
export function createSpellMenuState(initial={}){
 return {state:28,frame:0,selection:3,spell:1,fastEntry:false,leaving:false,inputDelay:30,spellStage:0,spellOrder:0,spellScroll:0,spellDifficulty:0,stageTransition:0,orderTransition:0,difficultyTransition:0,profileTransition:0,noticeClock:0,completeClock:0,noticePending:false,noticeRecord:null,noticeProfile:0,completePending:false,completeStage:0,completeProfile:0,completeFlags:[false,false,false,false,false,false,false],...initial};
}

// Native controller 52370..532d9. ANM/text refresh callbacks are synchronous
// services: callers must supply the actual presentation owners before using
// this controller in the title scene.
export function updateSpellPracticeMenu(initial,keys,{table,records,environment,fade=null,soundSlots=[-1,-1,-1],soundDisabled=false,music=null,services}={}){
 if(![28,29,30,31].includes(initial.state))throw Error('TH06nc: spell menu state required');
 const state=createSpellMenuState(initial),effects=[];
 const refresh=(kind,direction)=>{if(typeof services?.[kind]!=='function')throw Error('TH06nc: missing spell menu '+kind);services[kind](state,direction);};
 const sound=id=>queueSound(soundSlots,id,{disabled:soundDisabled});
 const edge=bit=>Boolean(keys.held&bit)&&((keys.held&bit)!==(keys.previous&bit));
 const move=bit=>Boolean(keys.held&bit)&&(edge(bit)||Boolean(keys.repeat));
 const select=(difficulty=state.spellStage===6?4:state.spellDifficulty)=>table.find(r=>r.stageIndex===state.spellStage&&r.order===state.spellOrder&&(difficulty<0||r.difficulty===difficulty))??null;
 const attempted=row=>row&&row.id<134&&Boolean(records.get(row.id)?.attempts);
 for(const name of Object.keys(spellMenuFields))if(state[name]>0)state[name]=(state[name]-1)|0;
 if(state.state===31){
  if(fade?.mode===2){environment.practice=false;environment.lifeProtection=false;environment.replayPlayback=false;environment.gameState=2;
   if(music&&music.handle!==-1){effects.push({kind:'stopMusic',handle:music.handle,mode:0},{kind:'releaseMusic',handle:music.handle});Object.assign(music,{handle:-1,playing:false,fading:false});}if(music)Object.assign(music,{pendingValue:0,requestActive:false});
   return {state,effects,soundSlots,launchReady:true};
  }return {state,effects,soundSlots,launchReady:false};
 }
 if(state.leaving){
  if(fade?.mode===2)Object.assign(state,{fastEntry:false,leaving:false,noticeClock:0,noticeRecord:null,completePending:false,completeClock:0,state:0,frame:0,spell:0,noticePending:false});
  return {state,effects,soundSlots,launchReady:false};
 }
 if(state.fastEntry&&(state.state!==28||state.frame>=54||[64,128,16,32].some(move)||edge(256)))state.fastEntry=false;
 const direction=move(64)?-1:move(128)?1:0;
 if(direction){
  state.noticePending=false;state.noticeRecord=null;state.completePending=false;
  const old=environment.character&255,profile=(((environment.character&255)*2+(environment.shot&255)+direction+4)|0)%4;
  environment.character=Math.trunc(profile/2)&255;environment.shot=(profile%2)&255;sound(12);
  if(old!==environment.character)refresh('stage',direction);
  refresh('profile',direction);refresh('info');
 }
 if(state.state===28){
  const old=state.spellStage;
  if(move(16))state.spellStage=((state.spellStage+6)|0)%7;
  if(move(32))state.spellStage=((state.spellStage+1)|0)%7;
  if(old!==state.spellStage)sound(12);
  if(state.frame>=state.inputDelay&&edge(256)){
   if(table.some(r=>r.stageIndex===state.spellStage&&attempted(r))){sound(10);environment.configuredSpellStage=state.spellStage;state.spellOrder=0;state.spellScroll=0;Object.assign(state,{state:29,frame:0,inputDelay:10});refresh('info');}
   else sound(11);
  }else if(edge(512)){
   state.leaving=true;sound(11);fade?.requestOut(0,30);state.selection=3;
  }
 }else if(state.state===29){
  const old=state.spellOrder,viewport=spellPracticeViewport(table,state.spellStage,state.spellOrder,state.spellScroll),count=viewport.count;state.spellScroll=viewport.start;
  if(count>0){
   if(move(16)){
    state.spellOrder=((state.spellOrder-1+count)|0)%count;
    if(old===0)state.spellScroll=Math.max(0,count-8);else if(state.spellOrder<viewport.start)state.spellScroll=state.spellOrder;
   }else if(move(32)){
    state.spellOrder=((state.spellOrder+1)|0)%count;
    if(state.spellOrder===0)state.spellScroll=0;else if(state.spellOrder>=viewport.start+8)state.spellScroll=state.spellOrder-7;
   }
  }
  if(old!==state.spellOrder){sound(12);refresh('info');}
  if(state.frame>=state.inputDelay&&edge(256)){
   if(spellPracticeOrderUnlocked(table,records,state.spellStage,state.spellOrder)){
    sound(10);Object.assign(state,{state:30,frame:0,inputDelay:10,spellDifficulty:0});
    const max=state.spellStage===6?1:4;for(let i=0;i<max;i++)if(select(state.spellStage===6?4:i)){state.spellDifficulty=i;break;}
    refresh('info');
   }else sound(11);
  }else if(edge(512)){sound(11);Object.assign(state,{state:28,frame:0,inputDelay:10});refresh('info');}
 }else{
  const max=state.spellStage===6?1:4,old=state.spellDifficulty;let delta=0;if(move(16))delta=-1;if(move(32))delta=1;
  if(delta){let candidate=old;for(let i=0;i<max;i++){candidate=((candidate+delta+max)|0)%max;if(select(state.spellStage===6?4:candidate))break;}if(candidate!==old){state.spellDifficulty=candidate;sound(12);}}
  if(state.frame>=state.inputDelay&&edge(256)){
   const row=select();if(attempted(row)){
    const profile=(environment.character&255)*2+(environment.shot&255);
    Object.assign(environment,{spellPractice:true,spellPracticeIndex:row.id,stageIndex:row.stageIndex,difficulty:row.difficulty,titleLaunchPending:true,spellWasCaptured:row.difficulty<5&&profile<4&&Boolean(records.get(row.id)?.practiceCaptures[row.difficulty*4+profile]),spellStageWasComplete:spellPracticeStageComplete(table,records,row.stageIndex,environment.character,environment.shot),lastSpellId:row.id,lastSpellProfile:profile&255,configuredSpellStage:state.spellStage});
    sound(10);fade?.requestOut(0,30);if(music){music.requestActive=false;if(music.playing){Object.assign(music,{fading:true,fadeStart:30,fadeFrame:30});effects.push({kind:'musicFade',frames:30});}}state.state=31;state.frame=0;
   }else sound(11);
  }else if(edge(512)){sound(11);Object.assign(state,{state:29,frame:0,inputDelay:10});refresh('info');}
 }
 if(state.noticePending&&state.state===28){state.noticePending=false;state.noticeRecord=null;}
 const profile=(environment.character&255)*2+(environment.shot&255),notice=state.noticeRecord;
 if(state.noticePending&&[29,30].includes(state.state)&&notice&&state.noticeProfile===profile&&notice.stageIndex===state.spellStage&&notice.order===state.spellOrder&&(!fade||fade.mode===0)){
  state.noticePending=false;state.noticeClock=60;sound(25);
 }
 if(state.completePending&&state.state===28&&state.completeProfile===profile&&state.completeStage>=0&&state.completeStage<=6&&state.completeFlags[state.completeStage]&&(!fade||fade.mode===0)){
  state.completePending=false;state.completeClock=60;sound(25);
 }
 return {state,effects,soundSlots,launchReady:false};
}
