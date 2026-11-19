export const scorePopupBytes=0x28;
// Normal 512-slot ring (9bd0) followed by the 3-slot score-item ring (436a7).
export class ScorePopupPool {
 constructor(){this.storage=new Uint8Array(515*scorePopupBytes);this.cursor=0;this.smallCursor=0;}
 publish({position,value,color=0xffffffff}){if(this.cursor>=512)this.cursor=0;const slot=this.cursor++;this.write(slot,position,value,color);return slot;}
 publishSmall({position,value}){if(this.smallCursor>=3)this.smallCursor=0;const slot=512+this.smallCursor++;this.write(slot,position,value,0xffffffff);return slot;}
 write(slot,position,value,color){
  const bytes=this.storage.subarray(slot*scorePopupBytes,(slot+1)*scorePopupBytes),v=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);value|=0;v.setUint8(0x1c,1);let count=0;
  if(value<0){v.setUint8(0x1d,10);count=1;}else{do{v.setUint8(0x1d+count,value%10);value=Math.trunc(value/10);count++;}while(value!==0);}
  v.setInt32(0,-999,true);v.setInt32(4,0,true);v.setUint32(8,color>>>0,true);v.setUint8(0xc,count);for(let k=0;k<3;k++)v.setFloat32(0x10+k*4,position[k],true);
 }
}
