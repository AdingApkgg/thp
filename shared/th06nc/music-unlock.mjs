// Native playback-request prefix 7bc9c..7bcf4, before cache/transport work.
// %d accepts a numeric prefix; an extension is not required by the format.
export function markMusicUnlocked(music,{ownerState=0,blocked=false,path=null}={}){
 if(!(music instanceof Uint8Array)||music.length!==16)throw Error('TH06nc music unlock: invalid MUSC owner');
 if(ownerState===9||blocked||path===null)return;
 const match=String(path).split('\0',1)[0].match(/^data\/bgm\/th06_[\t\n\v\f\r ]*([+-]?\d+)/);if(!match)return;
 // UCRT scans through a saturated signed 64-bit accumulator before storing
 // %d's low 32 bits (large positive/negative inputs do not wrap at 64 bits).
 let number=BigInt(match[1]);if(number>0x7fffffffffffffffn)number=0x7fffffffffffffffn;if(number< -0x8000000000000000n)number= -0x8000000000000000n;
 const id=Number(BigInt.asIntN(32,number));if(id<1||id>32)return;
 const view=new DataView(music.buffer,music.byteOffset,music.byteLength);view.setUint32(12,(view.getUint32(12,true)|(1<<(id-1)))>>>0,true);
}
