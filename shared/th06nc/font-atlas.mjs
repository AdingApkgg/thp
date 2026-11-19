// Native font cache loads advance_<key>.txt followed by the TexturePacker JSON.
// Advances can exist without a bitmap (notably space); absent glyphs advance 18.
export function readFontAtlas(json,advanceText){
 if(typeof json==='string')json=JSON.parse(json);if(!json||!Array.isArray(json.frames)||!json.meta?.size)throw Error('TH06nc font: invalid atlas metadata');
 const {w:width,h:height}=json.meta.size;if(!Number.isInteger(width)||!Number.isInteger(height)||width<=0||height<=0)throw Error('TH06nc font: invalid texture size');const glyphs=new Map();
 for(const line of advanceText.split(/\r?\n/)){if(!line)continue;const match=/^([0-9a-fA-F]{8})\t([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)$/.exec(line);if(!match)throw Error('TH06nc font: invalid advance record');const codePoint=parseInt(match[1],16),advance=Number(match[2]);if(codePoint>0x10ffff||!Number.isFinite(advance))throw Error('TH06nc font: invalid glyph advance');glyphs.set(codePoint,{codePoint,advance,x:0,y:0,width:0,height:0});}
 for(const frame of json.frames){
  if(!/^[0-9a-fA-F]{8}$/.test(frame.filename)||frame.rotated||frame.trimmed)throw Error('TH06nc font: unsupported glyph metadata');const codePoint=parseInt(frame.filename,16),r=frame.frame;if(!r||![r.x,r.y,r.w,r.h].every(Number.isInteger)||r.x<0||r.y<0||r.w<0||r.h<0||r.x+r.w>width||r.y+r.h>height)throw Error('TH06nc font: glyph rectangle outside texture');const glyph=glyphs.get(codePoint)??{codePoint,advance:0};Object.assign(glyph,{x:r.x,y:r.y,width:r.w,height:r.h});glyphs.set(codePoint,glyph);
 }
 return {width,height,image:json.meta.image,glyphs};
}
const toInt=x=>Number.isFinite(x)&&x>=-2147483648&&x<2147483648?Math.trunc(x):-2147483648;
// 7d455..7d624: integer blits and double-precision fractional advance carry.
export function layoutFontText(atlas,text,{x=0,y=0}={}){
 x|=0;y|=0;let current=x,fraction=0,width=0,height=0;const glyphs=[];
 for(const char of text){const codePoint=char.codePointAt(0);if(codePoint===0)break;const glyph=atlas.glyphs.get(codePoint);let advance=18;
  if(glyph){glyphs.push({codePoint,source:[glyph.x,glyph.y,glyph.width,glyph.height],position:[current,y]});width=(glyph.width-x+current)|0;height=Math.max(height,glyph.height);const integer=Math.trunc(glyph.advance);fraction+=glyph.advance-integer;advance=integer;if(fraction>=1){advance++;fraction-=1;}}
  current=toInt(current+advance);
 }
 return {glyphs,metrics:[x,y,width,height]};
}
