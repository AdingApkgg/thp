import {musicRoomTrackUnlocked} from './music-room-table.mjs';
export const musicRoomFields=Object.freeze({selection:0,playingIndex:0x2408,count:0x2420,exitClock:0x2428,pulse:0x242c,warnedIndex:0x2430,clock:0x2440,entryTicks:0x2444,scroll:0x2b08,state:0x3d10});
export const musicRoomAnimationOffsets=Object.freeze([0x2448,0x2568,0x2688,0x27a8,0x28c8,0x29e8]);

// Music-room input 57f30..5818e. Navigation uses edges only, including
// sequential Up+Down chords. Locked tracks show one warning, then play.
export function advanceMusicRoomInput(owner,{held=0,previous=0,records,unlockedMask=0,fade=null,publishDescription,playMusic}={}){
 const v=owner.v,get=key=>v.getInt32(musicRoomFields[key],true),set=(key,value)=>v.setInt32(musicRoomFields[key],value|0,true),edge=bit=>Boolean(held&bit)&&((held&bit)!==(previous&bit));
 if(edge(16)){
  const selected=(get('selection')-1)|0;set('selection',selected);
  if(selected<0){set('selection',get('count')-1);set('scroll',get('count')-10);}else if(get('scroll')>selected)set('scroll',selected);
 }
 if(edge(32)){
  const old=get('selection'),selected=(old+1)|0;set('selection',selected);
  if(selected>=get('count')){set('selection',0);set('scroll',0);}else if(get('scroll')<=((old-9)|0))set('scroll',old-8);
 }
 if(edge(16)||edge(32))set('warnedIndex',-1);
 if(edge(256)){
  const selected=get('selection'),row=records[selected];if(!row)throw Error('TH06nc music room: selected row missing');
  if(!musicRoomTrackUnlocked(row.file,unlockedMask)&&get('warnedIndex')!==selected){set('warnedIndex',selected);publishDescription('MD_LOCKED_DESC',false);}
  else{set('playingIndex',selected);v.setUint8(0x2425,1);playMusic(row.file);publishDescription(row.descriptionKey,false);}
 }
 if(edge(512)){
  for(const offset of [0x2712,0x2952,0x2832])v.setInt16(offset,2,true);
  v.setUint8(0x2424,1);set('exitClock',0);fade?.requestOut(0,30);
 }
 return false;
}

// Owner update 584a0..58623. The six background ANMs are always advanced;
// title return is based on the unsigned 30-tick exit counter, not fade mode.
export function advanceMusicRoom(owner,{environment={},advanceAnimation,...services}={}){
 const v=owner.v,get=key=>v.getInt32(musicRoomFields[key],true),set=(key,value)=>v.setInt32(musicRoomFields[key],value|0,true),animate=()=>{for(const offset of musicRoomAnimationOffsets)advanceAnimation(offset);};
 if(v.getUint8(0x2424)){
  animate();set('exitClock',get('exitClock')+1);if((get('exitClock')>>>0)>=30){environment.gameState=1;return 0;}return 1;
 }
 const previous=get('state');
 if(previous===0){if(get('clock')>=8)set('state',1);}else if(previous===1&&advanceMusicRoomInput(owner,services))return 0;
 if(previous!==get('state'))set('clock',0);else set('clock',get('clock')+1);
 if(!v.getUint8(0x2424)){if(get('entryTicks')<45)set('entryTicks',get('entryTicks')+1);set('pulse',((get('pulse')+1)|0)%72);}
 animate();return 1;
}
