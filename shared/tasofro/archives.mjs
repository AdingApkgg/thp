// Browser-compatible, read-only resource access for the later Tasofro engines.
// Format reference: brliron/135tk at 214fc81dc7dd662033009adfb63db4c3d39cf7ef
// (public domain). See NOTICE.txt. No original game data is included.
const MODULI=[
 'c79a9e9bfbc20cb0c3e7ae274967628a78bbd12cb24df487c70935f701f82ee5493b836b8426aa429ae1ccee08a2151c42e748b19cce7ad9401a4dd436375c89',
 'ff657274616952202d2d20696f6b6e616c46207373656c4220646f472079614d088bf4755d78b1c8937f40ea34a585c11b8d631775982da817453131514f6e8d',
 'c643e09d355e981dbe636d3a5f840f49b8e853f54206373b3625cb65cedd688cf75d720ac047bdfa3b104cd22cfe7203104dd885153555a35aafc34a3bf3e237',
 'c44d6a2f05782c0fd75c8297176091dd6f836181d14e069b9437d2984de47bbf4260a78f88d6fdfee1f56a0b29cf0bed66f0ac4ed7ef96068bfa8e3348a3027d'
].map(hex=>BigInt('0x'+hex));
const view=b=>new DataView(b.buffer,b.byteOffset,b.byteLength);
const u32=(b,p=0)=>view(b).getUint32(p,true);
const requireCondition=(yes,message)=>{if(!yes)throw Error(message);};
function powmod(value,exponent,modulus){let out=1n;for(;exponent;exponent>>=1n,value=value*value%modulus)if(exponent&1n)out=out*value%modulus;return out;}
function rsa(block,modulus){
 let n=0n;for(const b of block)n=n*256n+BigInt(b);
 n=powmod(n,65537n,modulus);const bytes=new Uint8Array(64);
 for(let i=63;i>=0;i--,n>>=8n)bytes[i]=Number(n&255n);
 if(bytes[0]!==0||bytes[1]!==1)return null;
 let i=2;while(i<63&&bytes[i]===255)i++;
 return i>=31&&bytes[i]===0?bytes.subarray(i+1):null;
}
function checkedReader(readAt,size){
 requireCondition(Number.isSafeInteger(size)&&size>=0,'invalid archive size');
 return async(offset,length)=>{
  requireCondition(Number.isSafeInteger(offset)&&Number.isSafeInteger(length)&&offset>=0&&length>=0&&offset<=size&&length<=size-offset,'archive range outside file');
  const bytes=await readAt(offset,length);
  requireCondition(bytes instanceof Uint8Array&&bytes.length===length,'short archive read');
  return bytes;
 };
}

// Hash raw Shift-JIS path bytes. ASCII callers may supply a string; non-ASCII
// callers must supply encoded bytes so a UTF-8 conversion cannot change hashes.
export function tfpkPathHash(path,version){
 requireCondition(version===0||version===1,'unsupported TFPK hash version');
 if(typeof path==='string'){
  requireCondition(/^[\x00-\x7f]*$/.test(path),'non-ASCII path requires Shift-JIS bytes');
  path=new TextEncoder().encode(path);
 }
 let hash=0x811c9dc5;
 for(let byte of path){if(byte>=65&&byte<=90)byte+=32;if(byte===47)byte=92;
  hash=version===0?(Math.imul(hash,0x1000193)^byte)>>>0:Math.imul(hash^byte,0x1000193)>>>0;}
 return version===0?hash:(-hash)>>>0;
}
async function inflateDefault(bytes,expected){
 const reader=new Blob([bytes]).stream().pipeThrough(new DecompressionStream('deflate')).getReader();
 const chunks=[];let length=0;
 try{for(;;){const {value,done}=await reader.read();if(done)break;length+=value.length;
  requireCondition(length<=expected,'filename table inflated beyond declared size');chunks.push(value);}}
 finally{await reader.cancel();}
 const result=new Uint8Array(length);let at=0;for(const chunk of chunks){result.set(chunk,at);at+=chunk.length;}
 return result;
}

export async function openTfpk(readAt,size,{inflate=inflateDefault}={}){
 const read=checkedReader(readAt,size),header=await read(0,5),version=header[4];
 requireCondition(String.fromCharCode(...header.subarray(0,4))==='TFPK'&&(version===0||version===1),'unsupported TFPK header');
 let at=5,modulus=null,cache=new Uint8Array(),cacheAt=0;
 const block=async()=>{
  if(at<cacheAt||at+64>cacheAt+cache.length){cacheAt=at;cache=await read(at,Math.min(65536,size-at));}
  requireCondition(at+64<=cacheAt+cache.length,'truncated RSA directory');
  const value=cache.subarray(at-cacheAt,at-cacheAt+64);at+=64;return value;
 };
 const field=async(length)=>{
  requireCondition(length>0&&length<=16*1024*1024,'invalid TFPK field size');
  const out=new Uint8Array(length);
  for(let pos=0;pos<length;pos+=32){
   const encrypted=await block();let plain;
   if(encrypted.subarray(32).every(b=>b===0))plain=encrypted.subarray(0,32);
   else if(modulus!==null)plain=rsa(encrypted,modulus);
   else for(const candidate of MODULI){plain=rsa(encrypted,candidate);if(plain){modulus=candidate;break;}}
   const n=Math.min(32,length-pos);
   requireCondition(plain&&plain.length>=n,`TFPK RSA padding/key validation failed at ${at-64}, field size ${length}`);out.set(plain.subarray(0,n),pos);
  }
  return out;
 };
 const directories=u32(await field(4));requireCondition(directories<=100000,'too many TFPK directories');
 for(let i=0;i<directories;i++)await field(8);
 const names=new Map();
 if(directories){
  const fn=await field(12),packed=u32(fn),unpacked=u32(fn,4),blocks=u32(fn,8);
  requireCondition(blocks>0&&blocks<=524288&&packed<=blocks*32&&unpacked<=16*1024*1024,'invalid TFPK filename table');
  const compressed=await field(blocks*32),plain=await inflate(compressed.subarray(0,packed),unpacked);
  requireCondition(plain.length===unpacked,'TFPK filename table size mismatch');
  for(let start=0;start<plain.length;){const end=plain.indexOf(0,start);requireCondition(end>=0,'unterminated TFPK filename');if(end===start)break;
   const raw=plain.subarray(start,end);names.set(tfpkPathHash(raw,version),new TextDecoder('shift_jis').decode(raw).replaceAll('\\','/'));start=end+1;}
 }
 const count=u32(await field(4));requireCondition(count>0&&count<=100000,'invalid TFPK file count');
 const entries=[];
 for(let i=0;i<count;i++){
  const info=await field(8),hashes=await field(version===0?4:8),key=await field(16);
  let bytes=u32(info),offset=u32(info,4),hash=u32(hashes);
  if(version===1){bytes=(bytes^u32(key))>>>0;offset=(offset^u32(key,4))>>>0;hash=(hash^u32(key,8))>>>0;
   for(let j=0;j<16;j+=4)view(key).setUint32(j,(-u32(key,j))>>>0,true);}
  entries.push({index:i,hash,name:names.get(hash)??null,bytes,offset,key});
 }
 const dataOffset=at;
 for(const entry of entries){entry.offset+=dataOffset;requireCondition(entry.offset<=size&&entry.bytes<=size-entry.offset,'TFPK entry outside archive');}
 return {format:'TFPK',version,entries,dataOffset,async readEntry(index){
  const e=entries[index];requireCondition(e,'unknown TFPK entry');
  const bytes=new Uint8Array(await read(e.offset,e.bytes)),aux=e.key.slice(0,4);
  for(let i=0;i<bytes.length;i++){const encrypted=bytes[i];bytes[i]^=e.key[i%16]^(version?aux[i%4]:0);aux[i%4]=encrypted;}
  return bytes;
 }};
}

// CG uses the Park-Miller recurrence. Quotients fit in 32 bits and the product
// below stays below 2^53, so integer Number arithmetic is exact here.
function cgStep(key){
 const b=Math.floor(key/44488);
 let value=(Math.imul(key-Math.imul(b,44488),48271)+Math.imul(b,-3399))|0;
 if(value<=0)value=(value+0x7fffffff)|0;
 return value>>>0;
}
export function decryptCg(input,offset){
 const bytes=new Uint8Array(input);let key=(bytes.length^offset)>>>0;
 for(let p=0;p<bytes.length;p+=4,key=(key+1)>>>0){let word=0,tmp=key;
  for(let j=0;j<4;j++){tmp=cgStep(tmp);word=(word<<8)|(tmp&255);}
  for(let j=0;j<Math.min(4,bytes.length-p);j++)bytes[p+j]^=(word>>>(j*8))&255;
 }
 return bytes;
}
export async function openCg(readAt,size){
 const read=checkedReader(readAt,size);requireCondition(size>=32,'truncated CG footer');
 const footer=decryptCg(await read(size-32,32),size-32);
 const count=u32(footer,24);
 requireCondition(u32(footer,20)===24&&u32(footer,28)===32&&count>0&&count<=100000,'unsupported CG footer');
 const tableOffset=size-32-count*24;
 const table=decryptCg(await read(tableOffset,count*24),tableOffset),entries=[];
 for(let i=0;i<count;i++){
  const p=i*24,hash=view(table).getBigUint64(p,true),offset=Number(view(table).getBigUint64(p+8,true)),bytes=Number(view(table).getBigUint64(p+16,true));
  requireCondition(Number.isSafeInteger(offset)&&Number.isSafeInteger(bytes)&&offset<=tableOffset&&bytes<=tableOffset-offset,'CG entry outside archive');
  entries.push({index:i,hash:hash.toString(16).padStart(16,'0'),offset,bytes});
 }
 return {format:'CG',entries,tableOffset,async readEntry(index){
  const e=entries[index];requireCondition(e,'unknown CG entry');const bytes=await read(e.offset,e.bytes);
  return e.hash==='000000001f47c0c8'?new Uint8Array(bytes):decryptCg(bytes,e.offset);
 }};
}
