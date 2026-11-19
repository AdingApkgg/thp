// Original fixed-packet Opus loader 7ea60 / packet reader 7ec80.
// This supplies Ogg framing without transcoding the original Opus packets.
export function readNativeOpus(bytes){
 if(!(bytes instanceof Uint8Array)||bytes.length<40)throw Error('TH06nc Opus: truncated header');
 const v=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),channels=v.getInt8(9),sampleRate=v.getUint32(12,true),packetStride=v.getInt16(10,true),preSkip=v.getInt16(28,true),offset=v.getInt32(16,true);
 if(v.getUint32(0,true)!==0x80000001||channels<1||channels>2||sampleRate!==48000||packetStride<=8||preSkip<0||offset<32||offset>bytes.length-8)throw Error('TH06nc Opus: unsupported header');
 const dataOffset=offset+8,dataLength=v.getInt32(offset+4,true);
 if(v.getUint32(offset,true)!==0x80000004||dataLength<0||dataLength>bytes.length-dataOffset||dataLength%packetStride!==0)throw Error('TH06nc Opus: invalid packet block');
 const packetCount=dataLength/packetStride,samples=Math.max(0,packetCount*960-preSkip);
 return {bytes,channels,sampleRate,packetStride,preSkip,dataOffset,dataLength,packetCount,samples};
}
export function nativeOpusPacket(stream,index){
 if(!Number.isInteger(index)||index<0||index>=stream.packetCount)throw Error('TH06nc Opus: packet outside stream');
 const offset=stream.dataOffset+index*stream.packetStride,v=new DataView(stream.bytes.buffer,stream.bytes.byteOffset+offset,stream.packetStride),declared=v.getInt32(0,false),length=declared>0&&declared<=stream.packetStride-8?declared:stream.packetStride-8;
 return stream.bytes.subarray(offset+8,offset+8+length);
}
const crcTable=Uint32Array.from({length:256},(_,i)=>{let crc=i<<24;for(let bit=0;bit<8;bit++)crc=(crc<<1)^((crc>>>31)?0x04c11db7:0);return crc>>>0;});
export function oggPage(packet,{serial=0x36434e54,sequence=0,granule=0,flags=0}={}){
 const segments=Math.floor(packet.length/255)+1;if(segments>255)throw Error('TH06nc Opus: Ogg packet too large');
 const bytes=new Uint8Array(27+segments+packet.length),v=new DataView(bytes.buffer);bytes.set(new TextEncoder().encode('OggS'));bytes[5]=flags;v.setBigUint64(6,BigInt(granule),true);v.setUint32(14,serial,true);v.setUint32(18,sequence,true);bytes[26]=segments;for(let i=0;i<segments;i++)bytes[27+i]=Math.min(255,packet.length-i*255);bytes.set(packet,27+segments);
 let crc=0;for(const byte of bytes)crc=((crc<<8)^crcTable[(crc>>>24)^byte])>>>0;v.setUint32(22,crc,true);return bytes;
}
export function nativeOpusToOgg(stream){
 const head=new Uint8Array(19),h=new DataView(head.buffer);head.set(new TextEncoder().encode('OpusHead'));head[8]=1;head[9]=stream.channels;h.setUint16(10,stream.preSkip,true);h.setUint32(12,48000,true);
 const vendor=new TextEncoder().encode('TH06nc packet framing'),tags=new Uint8Array(16+vendor.length),t=new DataView(tags.buffer);tags.set(new TextEncoder().encode('OpusTags'));t.setUint32(8,vendor.length,true);tags.set(vendor,12);
 const pages=[oggPage(head,{flags:2}),oggPage(tags,{sequence:1})];let length=pages[0].length+pages[1].length;
 for(let i=0;i<stream.packetCount;i++){const page=oggPage(nativeOpusPacket(stream,i),{sequence:i+2,granule:(i+1)*960,flags:i===stream.packetCount-1?4:0});pages.push(page);length+=page.length;}
 const output=new Uint8Array(length);let offset=0;for(const page of pages){output.set(page,offset);offset+=page.length;}return output;
}
