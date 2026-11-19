import {updateMarisaBBomb,drawMarisaBBomb} from './player-bomb-marisa-b.mjs';
import {updateMarisaABomb,drawMarisaABomb} from './player-bomb-marisa-a.mjs';
import {updateReimuBBomb,drawReimuBBomb} from './player-bomb-reimu-b.mjs';
import {updateReimuABomb,drawReimuABomb} from './player-bomb-reimu-a.mjs';
// Bomb branch inside player owner 689a8..68acb; caller clears damage widths
// before this branch, then continues the ordinary player life/movement owner.
export function advancePlayerBomb(player,input,{previousInput=0,messageField=-1,updateBomb=dispatchPlayerBomb,awardAchievement,commitAchievements,...services}={}){
 const {v,environment:env={}}=player;
 if(v.getUint8(0x9ec8)){updateBomb(player,services);return {active:Boolean(v.getUint8(0x9ec8)),started:false};}
 const callback=v.getBigUint64(0x9ed0,true),bombs=((env.bombs??0)<<24)>>24;
 if(messageField>=0||v.getInt32(0x773c,true)===0||bombs<=0||!(input&2)||(input&2)===(previousInput&2)||callback===0n)return {active:false,started:false};
 if(!env.replayPlayback&&v.getUint8(0x7898)===2){
  if(!awardAchievement||!commitAchievements)throw Error('TH06nc bomb: deathbomb achievement services missing');awardAchievement('Achievement20');commitAchievements();
 }
 env.bombs=((env.bombs??0)-1)&255;env.bombCount=((env.bombCount??0)+1)|0;env.inputFlags=((env.inputFlags??0)&~4)|8;
 v.setUint8(0x9ec8,1);v.setInt32(0x7ac4,0,true);v.setInt32(0x7ac0,-999,true);v.setInt32(0x9f20,999,true);updateBomb(player,services);
 env.spellActive=false;env.spellBombFlag=Boolean(env.spellCounter);
 return {active:Boolean(v.getUint8(0x9ec8)),started:true};
}
export function dispatchPlayerBomb(player,services={}){
 const callback=player.v.getBigUint64(0x9ed0,true);
 if(callback===0x14000e7f0n)return updateMarisaBBomb(player,services);
 if(callback===0x14000e270n)return updateMarisaABomb(player,services);
 if(callback===0x14000db50n)return updateReimuBBomb(player,services);
 if(callback===0x14000d1a0n)return updateReimuABomb(player,services);
 throw Error('TH06nc: player bomb callback not implemented: 0x'+callback.toString(16));
}
export function drawPlayerBomb(player,draw,services={}){
 const callback=player.v.getBigUint64(0x9ed8,true);
 if(callback===0x14000ebe0n)return drawMarisaBBomb(player,draw,services);
 if(callback===0x14000e650n)return drawMarisaABomb(player,draw,services);
 if(callback===0x14000e130n)return drawReimuBBomb(player,draw,services);
 if(callback===0x14000d9c0n)return drawReimuABomb(player,draw,services);
 throw Error('TH06nc: player bomb draw callback not implemented: 0x'+callback.toString(16));
}
