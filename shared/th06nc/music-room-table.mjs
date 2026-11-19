import {markMusicUnlocked} from './music-unlock.mjs';
export const musicRoomRecordBytes=0x84,musicRoomCapacity=32;

// musiccmt.txt parser 58b50. Copy bytes into the original zero-filled 32-row
// owner; field terminators are inherited from that owner rather than written.
export function readMusicRoomTable(input,{destination=new Uint8Array(0x1080)}={}){
 const source=input instanceof Uint8Array?input:new Uint8Array(input),bytes=destination;
 if(!(bytes instanceof Uint8Array)||bytes.length!==0x1080)throw Error('TH06nc music table: invalid owner');
 let at=0,index=-1;
 const finish=()=>{
  const count=index+1,text=(offset,size)=>{const field=bytes.subarray(offset,offset+size),zero=field.indexOf(0);return new TextDecoder().decode(zero<0?field:field.subarray(0,zero));};
  return {bytes,count,records:Array.from({length:count},(_,i)=>({titleKey:text(i*0x84,0x22),descriptionKey:text(i*0x84+0x22,0x22),file:text(i*0x84+0x44,0x40)}))};
 };
 while(at<source.length){
  if(source[at++]!==64)continue;
  if(++index>=32)throw Error('TH06nc music table: native allocation capacity exceeded');
  for(const field of [0x44,0,0x22]){
   let length=0,value=source[at]??0;
   while(value!==10&&value!==13){
    const target=index*0x84+field+length++;if(target>=bytes.length)throw Error('TH06nc music table: field exceeds owner');bytes[target]=value;
    if(++at>=source.length)return finish();value=source[at];
   }
   while(at<source.length&&(source[at]===10||source[at]===13))at++;
   if(at>=source.length)return finish();
  }
 }
 return finish();
}

// Music-room checks 58ed6/58055. Nonmatching/out-of-range paths are playable
// and visible; a valid track uses the MUSC bit without unlocking it here.
export function musicRoomTrackUnlocked(file,mask){
 const temporary=new Uint8Array(16);markMusicUnlocked(temporary,{path:file});const bit=new DataView(temporary.buffer).getUint32(12,true);
 return bit===0||Boolean((mask>>>0)&bit);
}
