export const endingStaffAssets=[['staff01.anm',49,0x620],['staff02.anm',50,0x627],['staff03.anm',51,0x62e]].map(([file,slot,base])=>({archive:'th06ED.dat',file,slot,base}));
// Native 2b7a0 script replacement used by @F; failure leaves the previous
// cursor and clock fields intact while the loaded-script pointer becomes 0.
export function replaceEndingScript(bytes,path,{loadScript,freeScript,reportError}={}){
 if(!(bytes instanceof Uint8Array)||bytes.length!==0x1280)throw Error('TH06nc ending: invalid owner');
 const v=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),previous=v.getBigUint64(8,true),loaded=loadScript(path);
 v.setBigUint64(8,BigInt(loaded??0),true);if(!loaded){reportError?.('endingFileLoadFailed');return -1;}
 v.setBigUint64(0x1250,BigInt(loaded),true);v.setInt32(0x18,8,true);
 for(const p of [0x1258,0x1260])v.setInt32(p,-999,true);for(const p of [0x125c,0x1264])v.setInt32(p,0,true);
 if(previous)freeScript(previous);return 0;
}
// Native 2caa6..2ce99, after CLRD has decided the restricted flag.
// Script ownership, achievements and error reporting are explicit services.
export function initializeEndingScript(bytes,e,{restricted=false,loadScript,freeScript,awardAchievement,commitAchievements,reportError}={}){
 if(!(bytes instanceof Uint8Array)||bytes.length!==0x1280)throw Error('TH06nc ending: invalid owner');
 const v=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),character=e.character&255,good=(e.difficulty|0)!==0&&!restricted;
 if(character<2){
  const shot=e.shot&255;
  // Native names are end00/end01/end10/end11 and end00b/end10b.
  const path=good?`data/end${character}${shot===0?0:1}.end`:`data/end${character}0b.end`,previous=v.getBigUint64(8,true),loaded=loadScript(path);
  v.setBigUint64(8,BigInt(loaded??0),true);
  if(!loaded){reportError?.('endingFileLoadFailed');return -1;}
  v.setBigUint64(0x1250,BigInt(loaded),true);v.setInt32(0x18,8,true);
  for(const p of [0x1258,0x1260])v.setInt32(p,-999,true);for(const p of [0x125c,0x1264])v.setInt32(p,0,true);
  if(previous)freeScript(previous);
  awardAchievement('Achievement'+String(good?14+character*2+(shot===0?0:1):13).padStart(2,'0'));commitAchievements();
 }
 const difficulty=e.difficulty|0;if(difficulty>=0&&difficulty<=3){awardAchievement('Achievement'+String(9+difficulty).padStart(2,'0'));commitAchievements();}
 if(e.lifeProtection){awardAchievement('Achievement18');commitAchievements();}
 else if((e.deathCount|0)===0){awardAchievement('Achievement19');commitAchievements();}
 return 0;
}
