// Native title's 4818b and 4b958 checks use exactly the three normal-table
// difficulties 1..3. Easy/Extra and the second CLRD table do not unlock Extra.
export function clearedUnlocks(bytes){
 if(!(bytes instanceof Uint8Array)||bytes.length!==96)throw Error('TH06nc unlocks: invalid CLRD owner');
 const shots=Array.from({length:2},(_,character)=>Array.from({length:2},(_,shot)=>[1,2,3].some(d=>bytes[(character*2+shot)*24+12+d]===99)));
 return {extraAvailable:shots.some(row=>row.some(Boolean)),extraUnlockedShots:shots};
}
