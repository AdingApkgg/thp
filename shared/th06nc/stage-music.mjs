// STD header metadata used directly by message music command 7 (3f56a/3f663).
// This reads four title keys and paths, not the stage's 3D background program.
export function readStageMusic(bytes){
 if(!(bytes instanceof Uint8Array)||bytes.byteLength<0x490)throw Error('TH06nc stage music: truncated STD header');const decoder=new TextDecoder('utf-8',{fatal:true}),string=offset=>{const raw=bytes.subarray(offset,offset+128),end=raw.indexOf(0);if(end<0)throw Error('TH06nc stage music: unterminated header field');return decoder.decode(raw.subarray(0,end));};return Array.from({length:4},(_,i)=>({titleKey:string(0x90+i*128),file:string(0x290+i*128)}));
}
