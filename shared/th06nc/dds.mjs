// TH06nc texture intake. BC7 blocks remain compressed for a capable renderer.
// No claim of GPU, color-space or pixel equivalence is made by this reader.
const check=(ok,s)=>{if(!ok)throw Error(`TH06nc DDS: ${s}`);};
export function readDds(bytes,{maxPixels=8192*8192}={}){
 check(bytes instanceof Uint8Array&&bytes.length>=128,'truncated header');
 const v=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),u=p=>v.getUint32(p,true);
 check(u(0)===0x20534444&&u(4)===124&&u(76)===32,'invalid header');
 const flags=u(8),height=u(12),width=u(16),mipCount=u(28)||1;
 check((flags&0x1007)===0x1007&&(u(108)&0x1000)!==0,'missing required flags');
 check(width>0&&height>0&&width*height<=maxPixels,'invalid or excessive dimensions');
 check(u(24)<=1&&(flags&0x800000)===0&&u(112)===0,'only flat 2D textures supported');
 check(mipCount<=1+Math.floor(Math.log2(Math.max(width,height))),'invalid mip count');
 check(mipCount===1||(flags&0x20000)!==0,'missing mip count flag');
 let offset=128,format,colorSpace='linear',compressed=false;
 if(u(80)===4&&u(84)===0x30315844){
  check(bytes.length>=148,'truncated DX10 header');
  check([98,99].includes(u(128)),'unsupported DXGI format');
  check(u(132)===3&&u(136)===0&&u(140)===1&&u(144)===0,'unsupported DX10 texture layout');
  format='BC7';colorSpace=u(128)===99?'srgb':'linear';compressed=true;offset=148;
 }else{
  check(u(80)===65&&u(84)===0&&u(88)===32&&u(92)===0xff0000&&u(96)===0xff00&&u(100)===255&&u(104)===0xff000000,'unsupported pixel format');
  format='RGBA8';
 }
 const levels=[];
 for(let i=0,w=width,h=height;i<mipCount;i++,w=Math.max(1,w>>1),h=Math.max(1,h>>1)){
  const rowBytes=compressed?Math.ceil(w/4)*16:w*4;
  const pitch=!compressed&&i===0&&(flags&8)?u(20):rowBytes;
  check(pitch>=rowBytes,'invalid row pitch');
  const length=pitch*(compressed?Math.ceil(h/4):h);
  check(length<=bytes.length-offset,'truncated pixel data');
  let data=bytes.subarray(offset,offset+length);
  if(!compressed){
   const rgba=new Uint8Array(w*h*4);
   for(let y=0;y<h;y++)for(let x=0;x<w;x++){
    const a=y*pitch+x*4,b=(y*w+x)*4;
    rgba[b]=data[a+2];rgba[b+1]=data[a+1];rgba[b+2]=data[a];rgba[b+3]=data[a+3];
   }
   data=rgba;
  }
  levels.push({width:w,height:h,data});offset+=length;
 }
 check(offset===bytes.length,'trailing pixel data');
 return {width,height,format,colorSpace,compressed,levels};
}
