// Strict MessagePack reader for JSON-shaped game resources. Extension values and
// non-string map keys are deliberately rejected instead of silently coerced.
export function readMessagePack(input,{maxDepth=128,maxContainerEntries=1000000}={}){
 const bytes=input instanceof Uint8Array?input:new Uint8Array(input),v=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),decoder=new TextDecoder('utf-8',{fatal:true});let offset=0,entries=0;
 const take=n=>{if(!Number.isSafeInteger(n)||n<0||offset+n>bytes.length)throw Error('TH06nc MessagePack: truncated value');const start=offset;offset+=n;return start;};
 const unsigned=n=>{const p=take(n);return n===1?v.getUint8(p):n===2?v.getUint16(p):v.getUint32(p);};
 const text=n=>{const p=take(n);return decoder.decode(bytes.subarray(p,p+n));};
 const container=n=>{entries+=n;if(entries>maxContainerEntries)throw Error('TH06nc MessagePack: container budget exceeded');};
 function array(n,depth){container(n);return Array.from({length:n},()=>value(depth+1));}
 function map(n,depth){
  container(n);const result=Object.create(null);
  for(let i=0;i<n;i++){const key=value(depth+1);if(typeof key!=='string'||Object.hasOwn(result,key))throw Error('TH06nc MessagePack: invalid or duplicate map key');result[key]=value(depth+1);}
  return result;
 }
 function integer64(signed){const p=take(8),x=signed?v.getBigInt64(p):v.getBigUint64(p);return x>=BigInt(Number.MIN_SAFE_INTEGER)&&x<=BigInt(Number.MAX_SAFE_INTEGER)?Number(x):x;}
 function value(depth){
  if(depth>maxDepth)throw Error('TH06nc MessagePack: nesting budget exceeded');const tag=unsigned(1);
  if(tag<=0x7f)return tag;if(tag>=0xe0)return tag-256;
  if(tag>=0xa0&&tag<=0xbf)return text(tag&31);if(tag>=0x90&&tag<=0x9f)return array(tag&15,depth);if(tag>=0x80&&tag<=0x8f)return map(tag&15,depth);
  switch(tag){
   case 0xc0:return null;case 0xc2:return false;case 0xc3:return true;
   case 0xc4:case 0xc5:case 0xc6:{const n=unsigned(2**(tag-0xc4)),p=take(n);return bytes.slice(p,p+n);}
   case 0xca:return v.getFloat32(take(4));case 0xcb:return v.getFloat64(take(8));
   case 0xcc:return unsigned(1);case 0xcd:return unsigned(2);case 0xce:return unsigned(4);case 0xcf:return integer64(false);
   case 0xd0:return v.getInt8(take(1));case 0xd1:return v.getInt16(take(2));case 0xd2:return v.getInt32(take(4));case 0xd3:return integer64(true);
   case 0xd9:return text(unsigned(1));case 0xda:return text(unsigned(2));case 0xdb:return text(unsigned(4));
   case 0xdc:return array(unsigned(2),depth);case 0xdd:return array(unsigned(4),depth);
   case 0xde:return map(unsigned(2),depth);case 0xdf:return map(unsigned(4),depth);
   default:throw Error(`TH06nc MessagePack: unsupported tag ${tag.toString(16)}`);
  }
 }
 const result=value(0);if(offset!==bytes.length)throw Error('TH06nc MessagePack: trailing bytes');return result;
}
