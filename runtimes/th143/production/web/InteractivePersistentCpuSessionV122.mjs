import{InteractivePersistentCpuSessionV121}from'./InteractivePersistentCpuSessionV121.mjs';
import{BrowserGlyphRasterV1}from'./BrowserGlyphRasterV1.mjs';
const base=new URL('./',import.meta.url);
export class InteractivePersistentCpuSessionV122 extends InteractivePersistentCpuSessionV121{
 async loadResource(url){
  if(typeof url==='string'&&/^\/(?:build\.json|play\.wasm|blobs\/[a-f0-9]{64}\.bin)$/.test(url))url=new URL(url.slice(1),base).href;
  return super.loadResource(url);
 }
 async initialize(progress=()=>{}){
  progress('载入日文字体');const bytes=await this.loadResource(new URL('fonts/NotoSansJP-Variable.ttf',base).href);this.ensureActive();
  if(await this.sha(bytes)!=='c2f3b4d463500a2ddcd3849cded1fceeb9fd6d1c32e6cbecd568453ba50fc68f')throw Error('Bundled font fingerprint changed');
  const font=new FontFace('TH143NotoJP',bytes,{weight:'100 900'});await font.load();this.ensureActive();document.fonts.add(font);this.browserGlyphFont=font;this.browserGlyphRaster=new BrowserGlyphRasterV1();
  return super.initialize(progress);
 }
 glyphsRequest(){
  const c=this.runtime,copy=(p,n)=>this.bytes(p,n).slice(),raster=this.browserGlyphRaster;
  if(!raster)throw Error('Browser text service is not ready');
  const output=raster.raster(copy(c.title_text_header(),108),copy(c.title_text_bitmap(),c.title_text_bitmap_bytes()),Array.from({length:13},(_,i)=>c.title_text_font_word(i)),Array.from({length:c.title_text_command_count()},(_,i)=>({color:c.title_text_command_word(i,0)>>>0,x:c.title_text_command_word(i,1)|0,y:c.title_text_command_word(i,2)|0,text:copy(c.title_text_command_data(i),c.title_text_command_word(i,3))})));
  this.bytes(c.title_text_bitmap(),output.length).set(output);++this.glyphs;return 1;
 }
}
