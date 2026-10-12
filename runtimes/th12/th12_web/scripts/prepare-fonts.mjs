// Offline Windows raster measurements; the browser loads data and C++ only.
import {FontOracle,fontParams,fontAnsiCodePage} from './native/font-oracle.mjs';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const root=fileURLToPath(new URL('../',import.meta.url)),th14=process.argv.includes('--title14'),out=th14?resolve(root,'../../th14/th14_web/assets/sdl-native/fonts'):resolve(root,'assets/sdl-native/fonts');mkdirSync(out,{recursive:true});
const sha=b=>createHash('sha256').update(b).digest('hex'),decoder=new TextDecoder('shift_jis'),mapping=Buffer.alloc(131072),chars=new Set();
for(let n=0;n<65536;++n){const b=n<256?Uint8Array.of(n):Uint8Array.of(n>>8,n&255),v=decoder.decode(b),c=v.length===1&&v!=='�'?v.charCodeAt(0):0x30fb;mapping.writeUInt16LE(c,n*2);if(c>=32&&c!==127&&c!==0x30fb)chars.add(c);}chars.add(0x30fb);
const fonts=[[32,400,'ＭＳ ゴシック'],[32,600,'ＭＳ 明朝'],[15,700,'ＭＳ ゴシック'],[15,700,'ＭＳ 明朝']];
if(th14)fonts.push([40,400,'ＭＳ ゴシック'],[40,600,'ＭＳ 明朝'],[15,700,'ＭＳ ゴシック'],[15,700,'ＭＳ 明朝']);
const params=(height,weight)=>{const p=fontParams(height,weight);if(th14)p[11]=2;return p;};
const faceBytes=face=>th14?Buffer.from(face==='ＭＳ ゴシック'?'826c827220835383568362834e':'826c82722096be92a9','hex'):null;
const oracle=new FontOracle(128,72),coverageOracle=new FontOracle(128,72,25),pairs=new Map(),baked=[],resolvedFaces=[];
try{
 for(let index=0;index<fonts.length;++index){const [height,weight,face]=fonts[index];coverageOracle.select(params(height,weight),face,faceBytes(face));resolvedFaces.push(coverageOracle.selectedFace());const glyphs=[];
  for(const code of [...chars].sort((a,b)=>a-b)){const char=String.fromCharCode(code);coverageOracle.pixels.fill(0x8000);const light=coverageOracle.draw(char,0xffffff,16,16).slice();coverageOracle.pixels.fill(0xffff);const dark=coverageOracle.draw(char,0,16,16);let left=128,top=72,right=0,bottom=0;
   for(let p=0;p<light.length;++p)if(light[p]!==0x8000){const x=p%128,y=Math.floor(p/128);left=Math.min(left,x);top=Math.min(top,y);right=Math.max(right,x+1);bottom=Math.max(bottom,y+1);}
   const advance=coverageOracle.advance(char),width=Math.max(0,right-left),rows=Math.max(0,bottom-top),channels=th14?3:1,coverage=Buffer.alloc(width*rows*channels);
   for(let y=top;y<bottom;++y)for(let x=left;x<right;++x){const p=y*128+x;if(light[p]===0x8000)continue;
    for(let channel=0;channel<channels;++channel){const shift=channel*5,l=(light[p]>>shift)&31,d=(dark[p]>>shift)&31;if(th14&&l===0&&d===31)continue;const key=(l<<5)|d;if(!pairs.has(key))pairs.set(key,{id:pairs.size+1,index,char,p,channel});coverage[((y-top)*width+x-left)*channels+channel]=pairs.get(key).id;}
   }
   glyphs.push({code,advance,left:width?left-16:0,top:rows?top-16:0,width,height:rows,coverage});
  }
  baked.push(glyphs);console.log(`Font ${index}: ${glyphs.length} glyphs`,JSON.stringify(fonts[index]));
 }
 if(pairs.size>255)throw Error('Unexpected GDI coverage classes');
 const blend=Buffer.alloc((pairs.size+1)*4096);
 for(const {id,index,char,p,channel}of pairs.values()){const [height,weight,face]=fonts[index];oracle.select(params(height,weight),face,faceBytes(face));
  for(let background=0;background<16;++background)for(let foreground=0;foreground<256;++foreground){oracle.pixels.fill(0xf000|background*0x111);oracle.draw(char,foreground*0x10101,16,16);blend[id*4096+background*256+foreground]=(oracle.pixels[p]>>(channel*4))&15;}
 }
 const files=[];function save(name,bytes){writeFileSync(resolve(out,name),bytes);files.push({file:name,bytes:bytes.length,sha256:sha(bytes)});}
 save('cp932.bin',mapping);save('blend4444.bin',blend);
 for(let index=0;index<fonts.length;++index){const glyphs=baked[index],offset=32+glyphs.length*20,total=offset+glyphs.reduce((n,g)=>n+g.coverage.length,0),bytes=Buffer.alloc(total);bytes.write('T11G');[1,index,fonts[index][0],glyphs.length,offset,total,0].forEach((n,i)=>bytes.writeUInt32LE(n,4+i*4));let at=offset;
  if(th14){bytes.writeUInt32LE(2,4);bytes.writeUInt32LE(3,28);}
  glyphs.forEach((g,i)=>{const p=32+i*20;bytes.writeUInt32LE(g.code,p);bytes.writeUInt32LE(at,p+4);bytes.writeInt16LE(g.advance,p+8);bytes.writeInt16LE(g.left,p+10);bytes.writeInt16LE(g.top,p+12);bytes.writeUInt16LE(g.width,p+14);bytes.writeUInt16LE(g.height,p+16);g.coverage.copy(bytes,at);at+=g.coverage.length;});save('font'+index+'.bin',bytes);
 }
 const fontSources=['msgothic.ttc','msmincho.ttc'].map(name=>resolve(process.env.WINDIR||'C:/Windows','Fonts',name)).filter(existsSync).map(p=>({file:p.split(/[\\/]/).pop(),sha256:sha(readFileSync(p))}));
 writeFileSync(resolve(out,'manifest.json'),JSON.stringify({format:th14?'T11G-v2-RGB':'T11G-v1',source:th14?'TH14 retail467940 CreateFontA exact parameters/raw CP932 face bytes, retail467ba0 font index order; offline host Windows GDI coverage. Font resolution depends on this host ANSI code page.':'TH11 1.00a 444480 CreateFont parameters; offline GDI ARGB4444 coverage',quality:th14?2:4,ansiCodePage:fontAnsiCodePage(),resolvedFaces,fonts,coverageClasses:pairs.size,fontSources,files},null,2)+'\n');
 console.log(JSON.stringify({fonts:fonts.length,glyphs:baked.reduce((n,g)=>n+g.length,0),coverageClasses:pairs.size,bytes:files.reduce((n,f)=>n+f.bytes,0)}));
}finally{oracle.close();coverageOracle.close();}
