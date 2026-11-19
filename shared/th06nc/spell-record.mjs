// Native spell record at 4f27c8 + ID*180, with byte-exact counters and arrays.
export function createSpellRecord(raw=null,{copy=true}={}){
 const bytes=raw?(copy?new Uint8Array(raw):raw):new Uint8Array(0x180);if(!(bytes instanceof Uint8Array)||bytes.length!==0x180)throw Error('TH06nc: invalid spell record size');const v=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);
 const record={bytes,history:bytes.subarray(0x13,0x18),scores:new Uint32Array(bytes.buffer,bytes.byteOffset+0x40,40),practiceAttempts:new Uint32Array(bytes.buffer,bytes.byteOffset+0xe0,20),practiceCaptures:new Uint32Array(bytes.buffer,bytes.byteOffset+0x130,20)};
 for(const [name,offset,width]of [['attempts',0x3c,2],['captures',0x3e,2],['checksum',0x12,1],['bonus',0xc,4]])Object.defineProperty(record,name,{enumerable:true,get:()=>width===1?v.getUint8(offset):width===2?v.getUint16(offset,true):v.getInt32(offset,true),set:x=>{if(width===1)v.setUint8(offset,x);else if(width===2)v.setUint16(offset,x,true);else v.setInt32(offset,x,true);}});
 Object.defineProperty(record,'key',{enumerable:true,get:()=>{const name=bytes.subarray(0x18,0x3c),end=name.indexOf(0);return new TextDecoder().decode(end<0?name:name.subarray(0,end));},set:key=>{const encoded=new TextEncoder().encode(key);if(encoded.length>=36)throw Error('TH06nc: spell record key exceeds name field');bytes.set(encoded,0x18);bytes[0x18+encoded.length]=0;}});
 return record;
}
export function materializeSpellRecord(record){
 if(record.bytes)return record;const result=createSpellRecord();
 for(const name of ['attempts','captures','checksum','bonus','key'])if(record[name]!==undefined)result[name]=record[name];
 for(const name of ['history','scores','practiceAttempts','practiceCaptures'])if(record[name])result[name].set(record[name]);return result;
}
