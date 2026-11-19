// Original sound table 3de430 (34 independent handles, 28 source WAVs).
// Queue consumer 76a30 stops at the first negative slot; volume zero preserves it.
export const soundFiles=['plst00','enep00','pldead00','power0','power1','tan00','tan01','tan02','ok00','cancel00','select00','gun00','cat00','lazer00','lazer01','enep01','nep00','damage00','item00','kira00','kira01','kira02','extend','timeout','graze','powerup','pause','fault'].map(name=>name+'.wav');
export const soundDefinitions=[[0,-1500],[0,-2000],[1,-1200],[1,-1400],[2,-1000],[3,-500],[4,-500],[5,-1700],[6,-1700],[7,-1700],[8,-1000],[9,-1000],[10,-1900],[11,-1200],[12,-900],[5,-1500],[13,-900],[14,-900],[15,-600],[16,-400],[17,-1100],[18,-900],[5,-1800],[6,-1800],[7,-1800],[19,-300],[20,-600],[21,-800],[22,-100],[23,-500],[24,-1000],[25,-1000],[26,-1000],[27,-400]].map(([source,attenuation])=>Object.freeze({file:soundFiles[source],source,attenuation}));
export function queueSound(slots,id,{disabled=false}={}){
 if(disabled)return;
 for(let i=0;i<3;i++){if(slots[i]<0){slots[i]=id;return;}if(slots[i]===id)return;}
}
export function consumeSoundQueue(slots,{volume=10,handles=soundDefinitions.map((_,i)=>i),setVolume,playSound}={}){
 if(!(volume&255))return 0;
 let count=0;
 for(let i=0;i<3;i++){
  const id=slots[i]|0;if(id<0)break;
  if(!soundDefinitions[id])throw Error('TH06nc sound: invalid queue ID '+id);
  slots[i]=-1;const handle=handles[id];if(handle===-1)continue;
  if(!setVolume||!playSound)throw Error('TH06nc sound: playback services missing');
  setVolume({handle,value:7300+(volume&255)*300+soundDefinitions[id].attenuation});
  playSound({handle,mode:1,restart:1});count++;
 }
 return count;
}
