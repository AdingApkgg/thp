// TH06 New Classic PKGL, reconstructed from the user's x64 executable.
// Native evidence: seed 0x140059e20; XOR 0x140059cb0; directory 0x140059fb0;
// file decode 0x14005a470. See tools/tests/test_th06nc_pkgl.py for native checks.
import {decompress} from '../vendor/fzstd/index.mjs';
const mask=(1n<<64n)-1n;
const check=(ok,message)=>{if(!ok)throw Error(message);};
export function archiveSeed(name){
 let stem=name.replaceAll('\\','/').split('/').at(-1),dot=stem.lastIndexOf('.');
 if(dot>=0)stem=stem.slice(0,dot);
 let crc=0xffffffff;
 for(const byte of new TextEncoder().encode(stem)){crc^=byte;for(let i=0;i<8;i++)crc=(crc>>>1)^((crc&1)?0xedb88320:0);}
 return (~crc)>>>0;
}
export function pkglKey(seed){
 const s=BigInt(seed>>>0);let state=((s<<32n)^(s*0x9e3779b1n+1n))&mask;
 const bytes=new Uint8Array(16);
 for(let i=0;i<2;i++){
  state=(state+0x9e3779b97f4a7c15n)&mask;let value=state;
  value=((value^(value>>30n))*0xbf58476d1ce4e5b9n)&mask;
  value=((value^(value>>27n))*0x94d049bb133111ebn)&mask;
  value^=value>>31n;
  for(let j=0;j<8;j++)bytes[i*8+j]=Number((value>>BigInt(j*8))&255n);
 }
 return bytes;
}
export function pkglDecrypt(input,seed){
 const bytes=new Uint8Array(input),key=pkglKey(seed);
 for(let i=0;i<bytes.length;i++)bytes[i]^=key[i&15];
 return bytes;
}
export async function openPkgl(readAt,size,archiveName,{maxEntryBytes=256*1024*1024}={}){
 check(Number.isSafeInteger(size)&&size>=8,'invalid PKGL archive size');
 const read=async(offset,length)=>{
  check(Number.isSafeInteger(offset)&&Number.isSafeInteger(length)&&offset>=0&&length>=0&&offset<=size&&length<=size-offset,'PKGL read outside archive');
  const bytes=await readAt(offset,length);check(bytes instanceof Uint8Array&&bytes.length===length,'short PKGL read');return bytes;
 };
 const head=await read(0,8),h=new DataView(head.buffer,head.byteOffset,8);
 check(h.getUint32(0,true)===0x4c474b50,'invalid PKGL magic');
 const length=h.getUint32(4,true);check(length>0&&length<=16*1024*1024,'invalid PKGL directory size');
 const table=pkglDecrypt(await read(8,length),archiveSeed(archiveName)),v=new DataView(table.buffer),entries=[];
 for(let p=0;p<table.length;){
  check(table.length-p>=32,'truncated PKGL record');
  const flags=v.getUint16(p,true),key=v.getUint32(p+2,true),bytes=Number(v.getBigUint64(p+6,true));
  const packed=Number(v.getBigUint64(p+14,true)),offset=Number(v.getBigUint64(p+22,true)),n=v.getUint16(p+30,true);p+=32;
  check(n>0&&n<256&&n<=table.length-p,'invalid PKGL filename length or incorrect archive name');
  const name=new TextDecoder('utf-8',{fatal:true}).decode(table.subarray(p,p+n));p+=n;
  check(!name.includes('\0'),'embedded NUL in PKGL filename');
  check(!(flags&~1),'unsupported PKGL flags');
  check(Number.isSafeInteger(bytes)&&bytes>=0&&bytes<=maxEntryBytes&&Number.isSafeInteger(offset)&&Number.isSafeInteger(packed)&&offset>=8+length&&offset<=size&&packed<=size-offset,'invalid PKGL entry extent');
  check((flags&1)||bytes===packed,'uncompressed PKGL size mismatch');
  entries.push({index:entries.length,name,flags,key,bytes,packed,offset});
 }
 return {format:'PKGL',entries,async readEntry(index){
  const e=entries[index];check(e,'unknown PKGL entry');
  let bytes=pkglDecrypt(await read(e.offset,e.packed),e.key);
  if(e.flags&1)bytes=decompress(bytes);
  check(bytes.length===e.bytes,'decoded PKGL size mismatch');return bytes;
 }};
}
