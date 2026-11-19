// Effect draw2b310 publishes world position to VM+c8 only for active slots.
// Replay dialogue restarts can omit a recording's intermediate draws. Retain
// raw hashes separately; omit only those inactive, last-drawn position bytes
// from this comparison copy. Active effects and the sentinel remain exact.
export function effectDrawIndependentBytes(bytes){
 if(!(bytes instanceof Uint8Array)||bytes.length!==513*0x198)throw Error('TH06nc effect comparison: invalid pool');
 const copy=bytes.slice();
 for(let slot=0;slot<512;slot++){
  const p=slot*0x198;
  if(copy[p+0x14]===0)copy.fill(0,p+0x108,p+0x114);
 }
 return copy;
}
