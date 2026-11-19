// Native message loader uses a u32 script count, followed by u32 file offsets.
// Records are u16 time/u8 opcode/u8 argument bytes; table entries can alias.
export function readMessage(bytes){
 if(!(bytes instanceof Uint8Array)||bytes.byteLength<8)throw Error('TH06nc message: truncated header');const v=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),count=v.getUint32(0,true),header=4+count*4;
 if(!count||count>65535||header>bytes.length)throw Error('TH06nc message: invalid script table');
 const offsets=Array.from({length:count},(_,i)=>v.getUint32(4+i*4,true));if(offsets.some(p=>p<header||p>bytes.length-4))throw Error('TH06nc message: script offset outside file');
 const starts=[...new Set(offsets)].sort((a,b)=>a-b),scripts=new Map();
 for(let i=0;i<starts.length;i++){
  const offset=starts[i],end=starts[i+1]??bytes.length,instructions=[];let p=offset;
  while(p<end){if(p+4>end)throw Error('TH06nc message: truncated command');const length=4+v.getUint8(p+3);if(p+length>end)throw Error('TH06nc message: command crosses script boundary');instructions.push({offset:p,time:v.getUint16(p,true),opcode:v.getUint8(p+2),length,args:bytes.subarray(p+4,p+length)});p+=length;}
  scripts.set(offset,{offset,end,instructions});
 }
 return {bytes,count,offsets,scripts:offsets.map(offset=>scripts.get(offset)),uniqueScripts:[...scripts.values()]};
}
