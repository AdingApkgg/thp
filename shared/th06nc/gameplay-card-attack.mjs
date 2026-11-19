// Native new-run CATK defaults at3aaf6..3abcd, before saved-record loading.
export function initializeRunCardAttackScores(destination,rng){
 if(!(destination instanceof Uint8Array)||destination.length!==134*384)throw Error('TH06nc CATK: invalid run owner');
 const view=new DataView(destination.buffer,destination.byteOffset,destination.byteLength);
 for(let id=0;id<134;id++){
  const start=id*384;
  for(let p=0;p<384;p+=2)view.setUint16(start+p,rng.next16(),true);
  view.setUint32(start,0x4b544143,true);view.setUint32(start+4,0x01800180,true);destination[start+8]=21;view.setUint16(start+16,id,true);view.setUint32(start+60,0,true);destination.fill(0,start+64,start+384);
 }
 return destination;
}
