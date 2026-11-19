import {SessionRenderer} from './SessionRendererHardwareV21.mjs';
// Full-session resources also use D3DFMT_A8. The pinned D3D9 HAL samples zero
// RGB with the stored alpha byte; retain native metadata after expansion.
export class SessionDevice extends SessionRenderer {
 uploadTexture(args,bytes){
  if(args[1]!==28)return super.uploadTexture(args,bytes);
  const[token,,width,height]=args;if(bytes.length!==width*height)throw Error('Invalid A8 texture size');
  const expanded=new Uint8Array(width*height*4);for(let i=0;i<bytes.length;i++)expanded[i*4+3]=bytes[i];
  const converted=[...args];converted[1]=21;super.uploadTexture(converted,expanded);this.textureInfo.get(token).format=28;
 }
}
