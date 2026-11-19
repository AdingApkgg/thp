const fail=message=>{throw Error('TH06nc score: '+message);},view=bytes=>new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),ror5=x=>(((x&255)>>>5)|(x<<3))&255;
const tagOf=bytes=>String.fromCharCode(...bytes.subarray(0,4));
// Original score.dat envelope: decrypt/validate 6ca60, write 74a3a..74aa2.
// Return owned bytes; callers may retain unknown records without discarding them.
export function decodeScoreFile(input){
 const bytes=new Uint8Array(input),v=view(bytes);if(bytes.length<24)fail('truncated file');let key=0,previous=bytes[1];
 for(let i=2;i<bytes.length;i++){key=ror5(key+previous);bytes[i]^=key;previous=bytes[i];}
 let checksum=0;for(let i=4;i<bytes.length;i++)checksum=(checksum+bytes[i])&65535;if(checksum!==v.getUint16(2,true))fail('checksum mismatch');
 const offset=v.getInt32(8,true),end=v.getInt32(0x10,true);if(offset<20||end<=offset||end>bytes.length)fail('invalid record extent');const records=[];
 for(let p=offset;p<end;){if(end-p<10)fail('truncated record');const size=v.getUint16(p+4,true);if(size<10||size>end-p)fail('invalid record size');records.push(bytes.slice(p,p+size));p+=size;}
 if(!records.some(r=>tagOf(r)==='TH6K'))fail('missing game marker');return {header:bytes.slice(0,offset),records,trailing:bytes.slice(end)};
}
export function encodeScoreFile({header=null,records,trailing=new Uint8Array()}={}){
 if(!Array.isArray(records)||!records.length||!records.some(r=>tagOf(r)==='TH6K'))fail('missing game marker');
 for(const r of records)if(!(r instanceof Uint8Array)||r.length<10||r.length>65535||view(r).getUint16(4,true)!==r.length)fail('invalid record size');
 const prefix=header?new Uint8Array(header):new Uint8Array(20);if(prefix.length<20)fail('invalid header');const end=prefix.length+records.reduce((n,r)=>n+r.length,0),bytes=new Uint8Array(end+trailing.length);if(bytes.length>0x7fffffff)fail('file too large');bytes.set(prefix);const v=view(bytes);if(!header)v.setUint16(4,0x15,true);v.setInt32(8,prefix.length,true);v.setInt32(0x10,end,true);v.setUint16(2,0,true);let p=prefix.length;
 for(const r of records){bytes.set(r,p);p+=r.length;}bytes.set(trailing,end);let checksum=0;for(let i=4;i<bytes.length;i++)checksum=(checksum+bytes[i])&65535;v.setUint16(2,checksum,true);
 let state=bytes[1];for(let i=2;i<bytes.length;i++){const plain=bytes[i],key=ror5(state);bytes[i]=plain^key;state=(key+plain)&255;}return bytes;
}
export function createScoreChunk(tag,size){
 if(typeof tag!=='string'||tag.length!==4||Array.from(tag,c=>c.charCodeAt(0)).some(c=>c>127)||!Number.isInteger(size)||size<10||size>65535)fail('invalid chunk');const bytes=new Uint8Array(size),v=view(bytes);bytes.set(Array.from(tag,c=>c.charCodeAt(0)));v.setUint16(4,size,true);v.setUint16(6,size,true);bytes[8]=0x15;return bytes;
}
export function createScoreFile(){return {header:new Uint8Array([0,0,0,0,21,0,0,0,20,0,0,0,0,0,0,0,32,0,0,0]),records:[createScoreChunk('TH6K',12)],trailing:new Uint8Array()};}
export function scoreChunkTag(bytes){return tagOf(bytes);}
