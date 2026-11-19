import {layoutFontText} from './font-atlas.mjs';
export function fontKey(size,colors,language){return `${size}_`+colors.map(x=>'0x'+(x>>>0).toString(16).toUpperCase().padStart(8,'0')).join('_')+(colors[0]===0xfffffe?'':'_'+language);}
// 7530: select font cache, repaint the bound ANM texture, write crop metrics,
// then make the VM visible. A missing native font cache preserves old metrics.
export function publishAnmText(vm,{text,colors,language='zh-CN',fonts,paint}={}){
 const {v}=vm,resource=vm.boundResource,sprite=vm.boundSprite;if(!resource||!sprite)throw Error('TH06nc text: bound destination sprite missing');if(!Array.isArray(colors)||colors.length!==4)throw Error('TH06nc text: four font colors required');
 const size=v.getUint8(0x108)||15,key=fontKey(size,colors,language),atlas=fonts?.get(key);let plan=null;
 if(atlas){
  if(!paint)throw Error('TH06nc text: texture painter missing');const x=Math.trunc(sprite.x),y=Math.trunc(sprite.y),layout=layoutFontText(atlas,text,{x,y});plan={key,target:resource,atlas,clear:[0,y,resource.width,36],glyphs:layout.glyphs,metrics:layout.metrics};paint(plan);
  layout.metrics.forEach((x,i)=>v.setInt32(0x10c+i*4,x,true));
 }
 v.setUint32(0xc4,v.getUint32(0xc4,true)|1,true);return plan;
}
