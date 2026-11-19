import {MusicRoomState} from './music-room-state.mjs';
import {initializeMusicRoom} from './music-room-initialize.mjs';
import {publishMusicRoomDescription} from './music-room-description.mjs';
import {advanceMusicRoom} from './music-room-update.mjs';
import {drawMusicRoom} from './music-room-draw.mjs';
import {createAsciiTextState} from './ascii-text.mjs';
import {NativeFade} from './fade.mjs';

export class MusicRoomScene {
 constructor(bank,{records,unlockedMask=0,localization={},publishText,playMusic,fade=new NativeFade(),environment={}}={}){
  this.state=new MusicRoomState(bank);this.fade=fade;this.ascii=createAsciiTextState(bank);this.environment=environment;this.previousInput=0;this.achievementRequests=[];this.descriptionKey=null;
  const publishDescription=(key,initial)=>{this.descriptionKey=key;publishMusicRoomDescription(this.state,key,{initial,localization,publishText});};
  this.services={records,unlockedMask,fade,environment,publishDescription,playMusic,advanceAnimation:offset=>this.state.vm(offset).tick()};
  initializeMusicRoom(this.state,{...this.services,localization,publishText,awardAchievement:key=>this.achievementRequests.push({kind:'award',key}),commitAchievements:()=>this.achievementRequests.push({kind:'commit'})});
 }
 tick(held=0){const status=advanceMusicRoom(this.state,{...this.services,held,previous:this.previousInput});this.previousInput=held;return status;}
 draw(draw){drawMusicRoom(this.state,draw,{ascii:this.ascii});}
 report(){const v=this.state.v;return {selection:v.getInt32(0,true),playingIndex:v.getInt32(0x2408,true),playing:Boolean(v.getUint8(0x2425)),count:v.getInt32(0x2420,true),scroll:v.getInt32(0x2b08,true),state:v.getInt32(0x3d10,true),clock:v.getInt32(0x2440,true),entryTicks:v.getInt32(0x2444,true),leaving:Boolean(v.getUint8(0x2424)),warnedIndex:v.getInt32(0x2430,true),descriptionKey:this.descriptionKey,achievementRequests:[...this.achievementRequests]};}
}
