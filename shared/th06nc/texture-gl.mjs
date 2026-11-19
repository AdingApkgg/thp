// Upload DDS levels without changing their declared color space or orientation.
// BC7 needs BPTC; unsupported devices fail explicitly until software fallback exists.
const uvScales=new WeakMap();
export const textureUvScale=texture=>uvScales.get(texture)??[1,1];
export function uploadDdsTexture(gl,dds){
 let internal=gl.RGBA8,extension=null;
 if(dds.compressed){
  extension=gl.getExtension('EXT_texture_compression_bptc');
  if(!extension)throw Error('TH06nc: BC7 requires EXT_texture_compression_bptc');
  internal=dds.colorSpace==='srgb'?extension.COMPRESSED_SRGB_ALPHA_BPTC_UNORM_EXT:extension.COMPRESSED_RGBA_BPTC_UNORM_EXT;
 }
 const texture=gl.createTexture();if(!texture)throw Error('TH06nc: texture allocation failed');
 try{
  const padded=dds.compressed&&(dds.width%4!==0||dds.height%4!==0);
  if(padded&&dds.levels.length!==1)throw Error('TH06nc: padded BC7 mip chain not yet supported');
  gl.bindTexture(gl.TEXTURE_2D,texture);
  gl.pixelStorei(gl.UNPACK_ALIGNMENT,1);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,false);gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL,false);
  gl.pixelStorei(gl.UNPACK_COLORSPACE_CONVERSION_WEBGL,gl.NONE);
  for(const [level,mip]of dds.levels.entries()){
   if(dds.compressed)gl.compressedTexImage2D(gl.TEXTURE_2D,level,internal,padded?Math.ceil(mip.width/4)*4:mip.width,padded?Math.ceil(mip.height/4)*4:mip.height,0,mip.data);
   else gl.texImage2D(gl.TEXTURE_2D,level,internal,mip.width,mip.height,0,gl.RGBA,gl.UNSIGNED_BYTE,mip.data);
  }
  gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAX_LEVEL,dds.levels.length-1);
  const error=gl.getError();if(error!==gl.NO_ERROR)throw Error(`TH06nc: texture upload GL error ${error}`);
  uvScales.set(texture,padded?[dds.width/(Math.ceil(dds.width/4)*4),dds.height/(Math.ceil(dds.height/4)*4)]:[1,1]);
  return texture;
 }catch(error){gl.deleteTexture(texture);throw error;}
}
