// Paint original glyph bitmaps into the mutable text.anm atlas. Canvas provides
// pixel-aligned source-over composition; native GPU pixel matching is separate.
export class FontTextureGl {
 constructor(gl){this.gl=gl;this.atlases=new Map();this.images=new Map();this.targets=new Map();this.paintCount=0;this.glyphCount=0;}
 register(key,atlas,dds){
  if(dds.compressed||dds.width!==atlas.width||dds.height!==atlas.height)throw Error('TH06nc font: RGBA bitmap matching metadata required');const canvas=new OffscreenCanvas(dds.width,dds.height),context=canvas.getContext('2d',{willReadFrequently:true});if(!context)throw Error('TH06nc font: canvas unavailable');context.putImageData(new ImageData(new Uint8ClampedArray(dds.levels[0].data),dds.width,dds.height),0,0);this.atlases.set(key,atlas);this.images.set(key,canvas);
 }
 target(resource){
  if(!this.targets.has(resource)){
   if(resource.textureName!=='@')throw Error('TH06nc font: destination is not a mutable ANM texture');const gl=this.gl,canvas=new OffscreenCanvas(resource.width,resource.height),context=canvas.getContext('2d',{willReadFrequently:true}),texture=gl.createTexture();if(!context||!texture)throw Error('TH06nc font: destination allocation failed');gl.bindTexture(gl.TEXTURE_2D,texture);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA8,resource.width,resource.height,0,gl.RGBA,gl.UNSIGNED_BYTE,null);for(const p of [gl.TEXTURE_MIN_FILTER,gl.TEXTURE_MAG_FILTER])gl.texParameteri(gl.TEXTURE_2D,p,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAX_LEVEL,0);this.targets.set(resource,{canvas,context,texture});
  }return this.targets.get(resource);
 }
 texture(resource){return this.target(resource).texture;}
 paint(plan){
  const image=this.images.get(plan.key);if(!image)throw Error('TH06nc font: bitmap not registered');const target=this.target(plan.target),context=target.context;context.imageSmoothingEnabled=false;context.clearRect(...plan.clear);let y0=plan.clear[1],y1=y0+plan.clear[3];
  for(const glyph of plan.glyphs){const [x,y,w,h]=glyph.source,[dx,dy]=glyph.position;if(w>0&&h>0){context.drawImage(image,x,y,w,h,dx,dy,w,h);y0=Math.min(y0,dy);y1=Math.max(y1,dy+h);}}
  y0=Math.max(0,y0);y1=Math.min(plan.target.height,y1);if(y1>y0){const gl=this.gl,pixels=context.getImageData(0,y0,plan.target.width,y1-y0).data;gl.bindTexture(gl.TEXTURE_2D,target.texture);gl.pixelStorei(gl.UNPACK_ALIGNMENT,1);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,false);gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL,false);gl.pixelStorei(gl.UNPACK_COLORSPACE_CONVERSION_WEBGL,gl.NONE);gl.texSubImage2D(gl.TEXTURE_2D,0,0,y0,plan.target.width,y1-y0,gl.RGBA,gl.UNSIGNED_BYTE,pixels);}
  this.paintCount++;this.glyphCount+=plan.glyphs.length;
 }
 clearTargets(){for(const target of this.targets.values())this.gl.deleteTexture(target.texture);this.targets.clear();}
 dispose(){this.clearTargets();this.images.clear();this.atlases.clear();}
}
