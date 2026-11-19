import {createScorePopupFont} from './score-popup-draw.mjs';
const F=Math.fround;
// ASCII manager 9790, formatted-text cache 9b07 and draw 9890.
// Formatting is supplied by callers; this cache accepts up to 63 Latin-1
// bytes per entry, the actual record's text capacity before its mode byte.
export function createAsciiTextState(anmBank){
 const bytes=new Uint8Array(0xdbb8),v=new DataView(bytes.buffer),font=createScorePopupFont(anmBank),popup=createScorePopupFont(anmBank);
 font.bindSprite(32);font.v.setFloat32(0xd0,0,true);bytes.set(font.state,0x10);bytes.set(popup.state,0x130);font.state=bytes.subarray(0x10,0x130);font.v=new DataView(bytes.buffer,0x10,0x120);
 v.setFloat32(0,1,true);v.setFloat32(4,1,true);v.setUint32(0x52cc,0xffffffff,true);return {bytes,v,font,anmBank};
}
export function enqueueAsciiText(state,{text,position,scale=null,color=null,camera=null,alternate=null}){
 const {v,bytes}=state,count=v.getInt32(0x7bb0,true);if(count>=256)return false;if(count<0)throw Error('TH06nc ASCII: invalid cache cursor');
 const encoded=Array.from(text,c=>c.charCodeAt(0));if(encoded.length>63||encoded.some(n=>n>255||n===0))throw Error('TH06nc ASCII: text exceeds Latin-1 record capacity');
 const p=0x7bb4+count*0x60;v.setInt32(0x7bb0,count+1,true);bytes.set([...encoded,0],p+0x1c);
 for(let i=0;i<3;i++)v.setFloat32(p+0x10+i*4,F(position[i]),true);
 v.setUint32(p+8,color??v.getUint32(0x52cc,true),true);for(let i=0;i<2;i++)v.setFloat32(p+i*4,F(scale?.[i]??v.getFloat32(i*4,true)),true);
 bytes[p+0xc]=camera??bytes[0x52c8];bytes[p+0x5c]=alternate??bytes[0x52c9];return true;
}
export function drawAsciiText(state,draw,{setupCamera=null}={}){
 const {v,bytes,font,anmBank}=state,a=font.v;a.setUint32(0xc4,(a.getUint32(0xc4,true)&0xfffffcff)|0x401,true);let camera=1;
 for(let slot=0;slot<v.getInt32(0x7bb0,true);slot++){
  const p=0x7bb4+slot*0x60;for(let i=0;i<3;i++)a.setUint32(0xc8+i*4,v.getUint32(p+0x10+i*4,true),true);
  a.setUint32(0xe8,v.getUint32(p,true),true);a.setUint32(0xe4,v.getUint32(p+4,true),true);const advance=F(v.getFloat32(p,true)*F(12));
  if(camera!==bytes[p+0xc]){camera=bytes[p+0xc];setupCamera?.({minZ:0,maxZ:1,perspective:Boolean(camera)});}
  for(let i=0;bytes[p+0x1c+i];i++){
   const c=bytes[p+0x1c+i];if(c===10){a.setFloat32(0xcc,F(F(v.getFloat32(p+4,true)*F(16))+a.getFloat32(0xcc,true)),true);a.setUint32(0xc8,v.getUint32(p+0x10,true),true);continue;}
   if(c!==32&&c>=32&&c<=129){const glyph=c+(bytes[p+0x5c]?98:-21);a.setUint32(0xec,v.getUint32(p+8,true),true);font.pointer(0x100,glyph+1);font.boundBinding=anmBank.sprites.get(glyph);draw(font,{snap:true,space:'screen',part:'ascii-text',slot,character:i,camera});}
   a.setFloat32(0xc8,F(advance+a.getFloat32(0xc8,true)),true);
  }
 }
 v.setInt32(0x7bb0,0,true);
}
