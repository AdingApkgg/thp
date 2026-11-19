import {musicRoomTrackUnlocked} from './music-room-table.mjs';
const F=Math.fround;
// Original 58cc0 resource/owner initializer after its four resources load.
// The host supplies localized font painting, description publication and the
// achievement service; the original ANMs and raw owner remain retained.
export function initializeMusicRoom(owner,{records,unlockedMask=0,localization={},publishText,publishDescription,awardAchievement=null,commitAchievements=null,fade=null}={}){
 for(let i=0;i<5;i++)owner.bind(0x2448+i*288,0x7d5+i);
 owner.bind(0x29e8,0x100);const v=owner.v;v.setInt32(0x2440,0,true);v.setInt32(0x242c,71,true);v.setInt32(0x2420,records.length,true);let unlocked=0;
 records.forEach((row,i)=>{
  const visible=musicRoomTrackUnlocked(row.file,unlockedMask),key=visible?row.titleKey:'MD_LOCKED_TITLE';if(visible)unlocked++;
  const offset=8+i*288,vm=owner.sprite(offset,0x101+i);publishText(vm,{offset,key,text:localization[key]??key,colors:[0xc0e0ff,0x302080,0x10101,0x40202]});
  vm.v.setFloat32(0xc8,93,true);vm.v.setFloat32(0xcc,F(F(F((i+1)*18)+F(104))-F(20)),true);vm.v.setFloat32(0xd0,0,true);vm.v.setUint32(0xc4,(vm.v.getUint32(0xc4,true)&~0x300)|0x400,true);
 });
 if(unlocked>=7){awardAchievement?.('Achievement22');commitAchievements?.();}
 v.setInt32(0x2430,-1,true);const first=records[0],playing=records[v.getInt32(0x2408,true)];if(!first||!playing)throw Error('TH06nc music room: no initial track');
 publishDescription(musicRoomTrackUnlocked(first.file,unlockedMask)?playing.descriptionKey:'MD_LOCKED_DESC',true);
 if(fade?.mode===2)fade.requestIn(0,30);return 0;
}
