// Original th06.cfg admission checks, 7b92b..7b99c. The ten key-binding
// bytes and untested tail are deliberately preserved rather than sanitized.
export function validGameConfig(bytes){
 if(!(bytes instanceof Uint8Array)||bytes.length!==44)return false;
 const v=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);
 if(v.getUint32(12,true)!==0x102)return false;
 for(const [offset,max]of [[16,4],[17,3],[18,9],[19,9],[20,1],[21,4],[22,1],[23,1],[24,1]])if(bytes[offset]>max)return false;
 return true;
}
export function acceptGameConfig(bytes){if(!validGameConfig(bytes))return null;const result=bytes.slice();result[0x28]=0;return {bytes:result,keys:bytes.slice(0,10)};}

// th06.env, 7b9f4..7ba5d. Window/render settings have a separate12-byte
// record and version gate; unused bytes survive accepted input unchanged.
export function validEnvironmentConfig(bytes){
 if(!(bytes instanceof Uint8Array)||bytes.length!==12)return false;
 if(new DataView(bytes.buffer,bytes.byteOffset,12).getUint32(0,true)!==0x102)return false;
 return bytes[4]<3&&bytes[5]<5&&bytes[6]<5&&bytes[7]<5&&bytes[8]<=1;
}

export const defaultEnvironmentConfig=()=>new Uint8Array([2,1,0,0,1,3,0,0,1,0,0,0]);
export function createGameConfig(){const bytes=new Uint8Array(44),keys=new Uint8Array([12,0,13,0,9,0,14,0,4,0]);resetGameConfig(bytes,keys);return bytes;}

// Reset at7bad0 preserves confirm/cancel swapping, name and final flag. Key
// bindings come from the runtime key owner, which the reset does not change.
export function resetGameConfig(bytes,keys){
 if(bytes.length!==44||keys.length!==10)throw Error('TH06nc config: invalid raw span');
 const buttonSwap=bytes[22],lastFlag=bytes[40],name=bytes.slice(32,40);bytes.fill(0);bytes.set(keys);new DataView(bytes.buffer,bytes.byteOffset,44).setUint32(12,0x102,true);bytes.set([2,3,7,7,0,1,0],16);bytes[22]=buttonSwap;bytes.set(name,32);bytes[40]=lastFlag;
}

