// TH06nc resource layout: native loader 0x1400020b0, sprites 0x1400024e0,
// script table 0x1400026cd. Reading commands does not execute them.
const check=(ok,s)=>{if(!ok)throw Error(`TH06nc ANM: ${s}`);};
export function readAnm(bytes){
 check(bytes instanceof Uint8Array&&bytes.length>=64,'truncated header');
 const v=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),u=p=>v.getUint32(p,true),f=p=>v.getFloat32(p,true);
 const ns=u(0),nc=u(4),tableEnd=64+ns*4+nc*8;
 check(tableEnd<=bytes.length,'truncated tables');
 check(Array.from({length:8},(_,i)=>u(32+i*4)).every(x=>x===0),'unsupported header variant');
 const width=u(12),height=u(16),nameOffset=u(28);
 check(width>0&&height>0,'invalid texture dimensions');
 check(nameOffset===tableEnd,'invalid texture name offset');
 const zero=bytes.indexOf(0,nameOffset);check(zero>=0,'unterminated texture name');
 const textureName=new TextDecoder('utf-8',{fatal:true}).decode(bytes.subarray(nameOffset,zero));
 const spriteOffsets=Array.from({length:ns},(_,i)=>u(64+i*4));
 const scriptHeaders=Array.from({length:nc},(_,i)=>({id:u(64+ns*4+i*8),offset:u(68+ns*4+i*8)}));
 let cursor=nameOffset+Math.ceil((zero-nameOffset+1)/16)*16;
 check(cursor<=bytes.length,'truncated name alignment');
 check(bytes.subarray(zero,cursor).every(x=>x===0),'nonzero name padding');
 const sprites=spriteOffsets.map(offset=>{
  check(offset===cursor&&offset+28<=bytes.length,'invalid sprite extent');cursor+=28;
  const values=Array.from({length:6},(_,i)=>f(offset+4+i*4));
  check(values.every(Number.isFinite),'nonfinite sprite data');
  return {id:u(offset),x:values[0],y:values[1],width:values[2],height:values[3],extra:values.slice(4)};
 });
 const scripts=scriptHeaders.map((h,i)=>{
  check(h.offset===cursor,'invalid script offset');
  const end=scriptHeaders[i+1]?.offset??bytes.length;
  check(end>cursor&&end<=bytes.length,'invalid script boundary');
  const instructions=[];let terminated=false;
  while(cursor<end){
   check(end-cursor>=4,'truncated command');
   const offset=cursor,time=v.getInt16(cursor,true),opcode=v.getUint8(cursor+2),length=v.getUint8(cursor+3);
   check(length<=end-cursor-4,'command crosses script boundary');
   cursor+=4+length;
   instructions.push({offset,time,opcode,args:bytes.subarray(offset+4,cursor)});
   if(opcode===0){check(length===0,'invalid stop command');terminated=true;break;}
  }
  check(terminated&&end-cursor<=4&&bytes.subarray(cursor,end).every(x=>x===0),'missing stop or invalid script padding');
  cursor=end;return {...h,instructions};
 });
 check(cursor===bytes.length,'trailing data');
 // Native tables assign IDs in file order; duplicates may overwrite earlier IDs.
 return {textureName,width,height,format:u(20),colorKey:u(24),sprites,scripts};
}
