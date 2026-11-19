// Original music request 7be52..7bea4: signed .pos samples at 44.1 kHz
// become signed 48 kHz sample positions by truncating (value * 480) / 441.
export function readMusicLoop(bytes){
 if(!(bytes instanceof Uint8Array)||bytes.byteLength!==8)throw Error('TH06nc music: invalid .pos metadata');
 const v=new DataView(bytes.buffer,bytes.byteOffset,8),source=[v.getInt32(0,true),v.getInt32(4,true)];
 return {source,start:Math.trunc(source[0]*480/441),end:Math.trunc(source[1]*480/441)};
}
