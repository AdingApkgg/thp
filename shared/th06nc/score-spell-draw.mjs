import {enqueueAsciiText} from './ascii-text.mjs';
const F=Math.fround;
// Inner spell table at 72df7..73165; background and main VMs are drawn by
// the common Result draw owner. All positions preserve native float32 steps.
export function drawScoreSpellTable(state,emit,{ascii,spellRecords,spellTable=[]}){
 const {v,bytes}=state,font=ascii.v,color=x=>font.setUint32(0x52cc,x,true),text=(value,position)=>enqueueAsciiText(ascii,{text:value,position});
 const x=F(v.getFloat32(0x1138,true)+F(88.88888549804688)),z=v.getFloat32(0x1140,true);let y=F(v.getFloat32(0x113c,true)+F(4));
 for(let row=0;row<10;row++){
  const index=v.getInt32(0x18,true)*10+row;if(index<0||index>=v.getInt32(0xa4,true))break;
  const id=bytes[0x1c+index],record=spellRecords.get(id),attempts=record?.attempts??0,captures=record?.captures??0,offset=0x2b70+row*288;
  v.setUint32(offset+0xc4,(v.getUint32(offset+0xc4,true)&~0x300)|0x400,true);v.setFloat32(offset+0xc8,x,true);v.setFloat32(offset+0xcc,F(y-F(5.444444179534912)),true);v.setFloat32(offset+0xd0,z,true);
  const rowColor=attempts===0?0x80c0c0ff:captures===0?0xffd0d0ff:(0xfff0f0ff-Math.imul(row,0x80800))>>>0;
  v.setUint32(offset+0xec,attempts===0?0x80c0c0ff:0xffffffff,true);
  const oldScale=[font.getUint32(0,true),font.getUint32(4,true)];font.setFloat32(0,F(.81),true);font.setFloat32(4,F(.81),true);color(0xffffffff);text('No.'+String(id+1).padStart(3,'0'),[x,F(y-F(5.502223014831543)),z]);
  v.setFloat32(offset+0xc8,F(x+F(96)),true);emit(offset);
  font.setFloat32(0,F(.7),true);font.setFloat32(4,F(.7),true);
  const difficulty=spellTable.find(r=>r.id===id)?.difficulty,sprite=difficulty!==undefined&&difficulty<=4?0x792+difficulty:0x797;state.vm(0x4310).bindSprite(sprite);
  v.setFloat32(0x43d8,F(x+F(2)),true);v.setFloat32(0x43dc,F(y+F(7.666666507720947)),true);v.setFloat32(0x43e0,z,true);v.setFloat32(0x43f4,F(.65),true);v.setFloat32(0x43f8,F(.65),true);v.setUint32(0x43fc,attempts?0xffffffff:0xff808080,true);emit(0x4310);
  color(rowColor);text(captures+'/'+attempts,[F(x+F(96)),F(y+F(7.555555820465088)),z]);y=F(y+F(31.33333396911621));oldScale.forEach((value,i)=>font.setUint32(i*4,value,true));
 }
}
