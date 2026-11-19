import{decodeDib,encodeDib}from'./BrowserGlyphRasterV1.mjs';
// TextRaster inverts its alpha before and after the service call. A glyph must
// change that inverted alpha even when its RGB is black (the outline passes).
export function compositeGlyphOverlay(header,input,overlay){
 const dib=decodeDib(header,input),rgba=dib.rgba.slice(),v=new DataView(header.buffer,header.byteOffset,header.byteLength),alphaMask=v.getUint32(52,true);
 if(overlay.length!==rgba.length)throw Error('Glyph coverage size changed');
 for(let i=0;i<rgba.length;i+=4){const coverage=overlay[i+3]/255;for(let c=0;c<3;c++)rgba[i+c]=Math.round(rgba[i+c]*(1-coverage)+overlay[i+c]*coverage);}
 const output=encodeDib(dib,rgba);
 if(alphaMask){
  let shift=0;while(shift<32&&!((alphaMask>>>shift)&1))++shift;const max=alphaMask>>>shift;
  if(!max||((max+1)&max))throw Error('Unsupported text alpha mask');
  const raw=new DataView(output.buffer),old=new DataView(input.buffer,input.byteOffset,input.byteLength);
  for(let y=0;y<dib.height;y++)for(let x=0;x<dib.width;x++){
   const coverage=overlay[(y*dib.width+x)*4+3];if(!coverage)continue;
   const at=(dib.signedHeight>0?dib.height-1-y:y)*dib.stride+x*(dib.bits/8),word=dib.bits===16?old.getUint16(at,true):old.getUint32(at,true),alpha=Math.round(((word&alphaMask)>>>shift)*(255-coverage)/255);
   const current=dib.bits===16?raw.getUint16(at,true):raw.getUint32(at,true),value=(current&~alphaMask)|((alpha<<shift)&alphaMask);
   if(dib.bits===16)raw.setUint16(at,value,true);else raw.setUint32(at,value>>>0,true);
  }
 }return output;
}
export class BrowserGlyphRasterV2{
 constructor(){this.canvas=document.createElement('canvas');this.context=this.canvas.getContext('2d',{willReadFrequently:true});if(!this.context)throw Error('Canvas text rendering unavailable');this.calls=0;this.draws=0;this.coveredPixels=0;}
 raster(header,input,font,draws){
  const dib=decodeDib(header,input),canvas=this.canvas,ctx=this.context;canvas.width=dib.width;canvas.height=dib.height;
  const size=Math.max(1,Math.abs(font[0]|0)),weight=Math.max(100,Math.min(900,font[4]||400));ctx.font=`${font[5]?'italic ':''}${weight} ${size}px TH143NotoJP`;ctx.textBaseline='alphabetic';
  const decoder=new TextDecoder(({128:'shift_jis',129:'euc-kr',134:'gbk',136:'big5',204:'windows-1251'})[font[8]]||'shift_jis');
  for(const draw of draws){const text=decoder.decode(draw.text),color=draw.color;ctx.fillStyle=`rgb(${color&255},${(color>>>8)&255},${(color>>>16)&255})`;ctx.fillText(text,draw.x,draw.y+size*.88);if(font[6]||font[7])ctx.fillRect(draw.x,draw.y+size*(font[7]?.5:.95),ctx.measureText(text).width,Math.max(1,size/16));}
  const overlay=ctx.getImageData(0,0,dib.width,dib.height).data;let covered=0;for(let i=3;i<overlay.length;i+=4)if(overlay[i])++covered;
  ++this.calls;this.draws+=draws.length;this.coveredPixels+=covered;return compositeGlyphOverlay(header,input,overlay);
 }
}
