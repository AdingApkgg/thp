const view=bytes=>new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);
function replayHeader(bytes){
 if(!(bytes instanceof Uint8Array)||bytes.length<120)throw Error('TH06nc replay: truncated header');
 const v=view(bytes);if(v.getUint32(0,true)!==0x50523654||v.getUint16(4,true)!==0x10f)throw Error('TH06nc replay: unsupported signature/version');return v;
}
export function replayChecksum(bytes){let sum=0x2f10a329;for(let i=18;i<bytes.length;i++)sum=(sum+bytes[i])>>>0;return sum;}
function stageOffsets(bytes){const v=view(bytes),offsets=[];for(let i=0;i<7;i++){const p=v.getBigUint64(64+i*8,true);if(p!==0n&&(p<120n||p>=BigInt(bytes.length)))throw Error('TH06nc replay: stage offset outside file');offsets.push(p===0n?null:Number(p));}return offsets;}
// 6af60 decode and 6b110 checksum. JS retains relative stage offsets rather
// than native heap pointers. Reject truncated/out-of-file offsets before use.
export function decodeReplayFile(input){
 replayHeader(input);const bytes=input.slice(),v=view(bytes);let key=bytes[18];for(let i=19;i<bytes.length;i++){bytes[i]=(bytes[i]-key)&255;key=(key+7)&255;}
 const checksum=v.getUint32(12,true);if(replayChecksum(bytes)!==checksum)throw Error('TH06nc replay: checksum mismatch');
 bytes[28]=0;bytes[37]=0;const offsets=stageOffsets(bytes);v.setUint32(12,0,true);return {bytes,header:bytes.subarray(0,120),stageOffsets:offsets,checksum};
}
// Writer 6c908..6c93f, after its stage-data assembly and pointer-to-offset pass.
// This serializes an assembled replay; it does not manufacture recording data.
export function encodeReplayFile(input,{seed=input?.[18]}={}){
 replayHeader(input);stageOffsets(input);if(!Number.isInteger(seed)||seed<0||seed>255)throw Error('TH06nc replay: invalid cipher seed');
 const bytes=input.slice(),v=view(bytes);bytes[18]=seed;v.setUint32(12,replayChecksum(bytes),true);let key=seed;for(let i=19;i<bytes.length;i++){bytes[i]=(bytes[i]+key)&255;key=(key+7)&255;}return bytes;
}
