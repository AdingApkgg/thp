import {readStageMusic} from './stage-music.mjs';
// Original loader 786bb..78754, primitive traversal 787f0..78918 and
// fixed 20-byte camera records at 77c09/77dea. Offsets stay file-relative.
export function readStd(bytes){
 if(!(bytes instanceof Uint8Array)||bytes.byteLength<0x494)throw Error('TH06nc STD: truncated header');
 const v=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),objectCount=v.getInt16(0,true),primitiveCount=v.getInt16(2,true),instancesOffset=v.getInt32(4,true),scriptOffset=v.getInt32(8,true),headerEnd=0x490+objectCount*4;
 if(objectCount<0||primitiveCount<0||headerEnd>bytes.length||instancesOffset<headerEnd||scriptOffset<instancesOffset+16||scriptOffset>bytes.length-20)throw Error('TH06nc STD: invalid header');
 const text=new TextDecoder('utf-8',{fatal:true}),string=p=>{const b=bytes.subarray(p,p+128),end=b.indexOf(0);if(end<0)throw Error('TH06nc STD: unterminated header field');return text.decode(b.subarray(0,end));},vec=p=>Array.from({length:3},(_,i)=>v.getFloat32(p+i*4,true));
 const offsets=Array.from({length:objectCount},(_,i)=>v.getInt32(0x490+i*4,true)),primitives=[];
 const objects=offsets.map((offset,index)=>{
  const end=offsets[index+1]??instancesOffset;if(offset<headerEnd||offset+30>end||end>instancesOffset)throw Error('TH06nc STD: invalid object range');const faces=[];let p=offset+28;
  while(true){if(p+2>end)throw Error('TH06nc STD: missing primitive terminator');const type=v.getInt16(p,true);if(type<0)break;if(p+8>end)throw Error('TH06nc STD: truncated primitive');const length=v.getInt16(p+2,true);if(type!==0||length!==28||p+length>end)throw Error('TH06nc STD: unsupported or truncated primitive');const face={offset:p,type,length,anmIndex:v.getInt16(p+4,true),vmIndex:v.getUint16(p+6,true),position:vec(p+8),size:[v.getFloat32(p+20,true),v.getFloat32(p+24,true)]};faces.push(face);primitives.push(face);p+=length;}
  return {offset,id:v.getUint16(offset,true),unknown:v.getUint8(offset+2),flags:v.getUint8(offset+3),position:vec(offset+4),size:vec(offset+16),primitives:faces};
 });
 if(primitives.length!==primitiveCount)throw Error('TH06nc STD: primitive count mismatch');
 const instances=[];let p=instancesOffset;for(;;p+=16){if(p+16>scriptOffset)throw Error('TH06nc STD: missing instance terminator');const objectIndex=v.getInt16(p,true);if(objectIndex<0)break;if(objectIndex>=objectCount)throw Error('TH06nc STD: instance object outside table');instances.push({offset:p,objectIndex,flags:v.getUint16(p+2,true),position:vec(p+4)});}
 const instructions=[];for(p=scriptOffset;;p+=20){if(p+20>bytes.length)throw Error('TH06nc STD: missing script terminator');const time=v.getInt32(p,true),opcode=v.getInt16(p+4,true),argumentBytes=v.getUint16(p+6,true);if(time===-1&&opcode===-1)break;if(opcode<0||opcode>5||argumentBytes!==12)throw Error('TH06nc STD: invalid camera instruction');instructions.push({offset:p,time,opcode,argumentBytes,args:bytes.subarray(p+8,p+20)});}
 return {bytes,objectCount,primitiveCount,instancesOffset,scriptOffset,unknown:v.getUint32(12,true),stageName:string(16),musicTracks:readStageMusic(bytes),objects,primitives,instances,instructions};
}
