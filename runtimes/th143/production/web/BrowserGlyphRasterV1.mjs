// Browser implementation of the bitmap/text service boundary. Game text bytes,
// commands and DIB dimensions remain owned by the native runtime.
export function decodeDib(header,input){
 const v=new DataView(header.buffer,header.byteOffset,header.byteLength),width=v.getInt32(4,true),signedHeight=v.getInt32(8,true),height=Math.abs(signedHeight),bits=v.getUint16(14,true);
 if(header.length<108||width<=0||height<=0||![16,32].includes(bits))throw Error('Unsupported text DIB');
 const stride=Math.ceil(width*bits/32)*4;
 if(stride*height!==input.length||input.length>16*1024*1024)throw Error('Invalid text DIB size');
 const masks=[40,44,48].map((at,i)=>v.getUint32(at,true)|| (bits===16?[0x7c00,0x3e0,0x1f]:[0xff0000,0xff00,0xff])[i]);
 const channels=masks.map(mask=>{let shift=0;while(shift<32&&!((mask>>>shift)&1))++shift;const max=mask>>>shift;if(!max||((max+1)&max))throw Error('Unsupported DIB channel mask');return{mask,shift,max};});
 const raw=new DataView(input.buffer,input.byteOffset,input.byteLength),rgba=new Uint8ClampedArray(width*height*4);
 for(let y=0;y<height;y++)for(let x=0;x<width;x++){
  const at=(signedHeight>0?height-1-y:y)*stride+x*(bits/8),word=bits===16?raw.getUint16(at,true):raw.getUint32(at,true),pixel=(y*width+x)*4;
  channels.forEach((c,i)=>rgba[pixel+i]=Math.round(((word&c.mask)>>>c.shift)*255/c.max));rgba[pixel+3]=255;
 }
 return{width,height,signedHeight,bits,stride,channels,rgba,input};
}
export function encodeDib(dib,rgba){
 const{width,height,signedHeight,bits,stride,channels,input}=dib,output=input.slice(),raw=new DataView(output.buffer),mask=channels.reduce((a,c)=>a|c.mask,0);
 for(let y=0;y<height;y++)for(let x=0;x<width;x++){
  const at=(signedHeight>0?height-1-y:y)*stride+x*(bits/8),pixel=(y*width+x)*4;let word=(bits===16?raw.getUint16(at,true):raw.getUint32(at,true))&~mask;
  channels.forEach((c,i)=>word|=(Math.round(rgba[pixel+i]*c.max/255)<<c.shift)&c.mask);
  if(bits===16)raw.setUint16(at,word,true);else raw.setUint32(at,word>>>0,true);
 }return output;
}
export class BrowserGlyphRasterV1{
 constructor(){this.canvas=document.createElement('canvas');this.context=this.canvas.getContext('2d',{willReadFrequently:true});if(!this.context)throw Error('Canvas text rendering unavailable');this.calls=0;this.draws=0;}
 raster(header,input,font,draws){
  const dib=decodeDib(header,input),canvas=this.canvas,ctx=this.context;canvas.width=dib.width;canvas.height=dib.height;
  ctx.putImageData(new ImageData(dib.rgba,dib.width,dib.height),0,0);
  const size=Math.max(1,Math.abs(font[0]|0)),weight=Math.max(100,Math.min(900,font[4]||400));
  ctx.font=`${font[5]?'italic ':''}${weight} ${size}px TH143NotoJP`;ctx.textBaseline='alphabetic';
  const decoder=new TextDecoder(({128:'shift_jis',129:'euc-kr',134:'gbk',136:'big5',204:'windows-1251'})[font[8]]||'shift_jis');
  for(const draw of draws){
   const text=decoder.decode(draw.text),color=draw.color;ctx.fillStyle=`rgb(${color&255},${(color>>>8)&255},${(color>>>16)&255})`;
   ctx.fillText(text,draw.x,draw.y+size*.88);
   if(font[6]||font[7]){const w=ctx.measureText(text).width;ctx.fillRect(draw.x,draw.y+size*(font[7]?.5:.95),w,Math.max(1,size/16));}
  }
  ++this.calls;this.draws+=draws.length;return encodeDib(dib,ctx.getImageData(0,0,dib.width,dib.height).data);
 }
}
