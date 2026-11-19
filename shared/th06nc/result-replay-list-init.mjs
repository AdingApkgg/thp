import {queueSound} from './sound-queue.mjs';
// Replay-list entry 6d310..6d451, including the real 6d1e0 state reset.
// readHeader supplies the validated/decrypted 120-byte header from 6af60;
// absent files preserve the previous slot, as the native copy loop does.
export function initializeResultReplayList({v,bytes},{soundSlots=[-1,-1,-1],soundDisabled=false,ensureDirectory=null,readHeader=null}={}){
 queueSound(soundSlots,10,{disabled:soundDisabled});v.setInt32(0x9e94,12,true);
 for(let i=0;i<38;i++)v.setInt16(0xb0+i*288+0x8a,10,true);
 v.setInt32(0x9e7c,v.getInt32(0x4438,true),true);v.setInt32(0x4450,0,true);loadResultReplayHeaders({bytes},{ensureDirectory,readHeader});
}
export function loadResultReplayHeaders({bytes},{ensureDirectory=null,readHeader=null}={}){
 ensureDirectory?.('replay');
 for(let slot=1;slot<=60;slot++){
  const header=readHeader?.(`replay/th6_${String(slot).padStart(2,'0')}.rpy`,slot);
  if(header!=null){if(!(header instanceof Uint8Array)||header.length<120)throw Error('TH06nc replay: validated header is truncated');bytes.set(header.subarray(0,120),0x9eb0+(slot-1)*120);}
 }
}
