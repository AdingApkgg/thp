// Structural reader for the seven ECL resources shipped with TH06 New Classic.
// This is not an interpreter: opcode 200/201 and all gameplay semantics require
// native evidence before an executor may claim compatibility with this title.
const check=(ok,message)=>{if(!ok)throw Error(`TH06nc ECL: ${message}`);};
export function readEcl(bytes){
 check(bytes instanceof Uint8Array&&bytes.length>=16,'truncated header');
 const v=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);
 const count=v.getUint16(0,true),reserved=v.getUint16(2,true),tableEnd=16+count*4;
 check(count>0&&tableEnd<=bytes.length,'invalid subroutine table');
 check(reserved===0,'unsupported header variant');
 const timelines=Array.from({length:3},(_,i)=>v.getUint32(4+i*4,true));
 const offsets=Array.from({length:count},(_,i)=>v.getUint32(16+i*4,true));
 const starts=[...offsets,...timelines.filter(Boolean)].sort((a,b)=>a-b);
 check(starts[0]===tableEnd,'gap before script data');
 check(starts.every((p,i)=>p>=tableEnd&&p<bytes.length&&(!i||p>starts[i-1])),'invalid or overlapping script offsets');
 const endByStart=new Map(starts.map((p,i)=>[p,starts[i+1]??bytes.length]));
 const walk=(start,timeline)=>{
  const end=endByStart.get(start),instructions=[];let p=start,terminated=false;
  while(p<end){
   const headerBytes=timeline?8:12;
   check(end-p>=(timeline?4:12),'truncated instruction header');
   const time=timeline?v.getInt16(p,true):v.getInt32(p,true);
   if(timeline&&time===-1){check(p+4===end,'trailing bytes after timeline sentinel');p+=4;terminated=true;break;}
   check(end-p>=headerBytes,'truncated instruction header');
   const opcode=v.getInt16(p+4,true),length=v.getUint16(p+6,true);
   check(length>=headerBytes&&length<=end-p,'instruction crosses script boundary');
   if(!timeline&&opcode===-1){
    check(time===-1&&length===12&&p+length===end,'invalid subroutine sentinel');
    p+=length;terminated=true;break;
   }
   check(opcode>=0,'negative opcode');
   instructions.push({offset:p,time,opcode,length,
    ...(timeline?{arg0:v.getInt16(p+2,true)}:{difficultyMask:v.getUint8(p+9),flags:v.getUint16(p+10,true)}),
    args:bytes.subarray(p+headerBytes,p+length)});
   p+=length;
  }
  check(terminated&&p===end,'missing script sentinel');
  return {offset:start,end,instructions};
 };
 return {format:'TH06nc ECL',subroutines:offsets.map(p=>walk(p,false)),
  timelines:timelines.map(p=>p?walk(p,true):null)};
}
