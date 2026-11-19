// 2D geometry: cropped 2af1 or ordinary 2ba1..2e05, rotated 37a5.
// Returns strip order TL, TR, BL, BR in physical framebuffer coordinates.
const F=Math.fround;
const rint=x=>{const low=Math.floor(x),d=x-low;const n=d<0.5?low:d>0.5?low+1:low%2===0?low:low+1;return n===0&&x<0?-0:n;};
export function anmQuad(vm,height=1080,{snap=false}={}){
 const v=vm.v,flags=v.getUint32(0xc4,true),resource=vm.boundResource??vm.resource;
 if(vm.boundBinding?.active===false)return null;
 if((flags&3)!==3||v.getUint32(0xec,true)===0||!vm.pointer(0x100))return null;
 const angle=v.getFloat32(0xa4,true),rotated=angle!==0;
 // Native 36c0's rotated path ignores the crop rectangle entirely.
 const cropped=!rotated&&v.getInt32(0x114,true)>0;
 const s=vm.boundSprite??resource.sprites.findLast(s=>s.id===v.getUint16(0x34,true));if(!s)return null;
 const width=cropped?F(v.getInt32(0x114,true)):rotated?F(s.width):F(F(s.x+s.width)-s.x),h=cropped?F(v.getInt32(0x118,true)):rotated?F(s.height):F(F(s.y+s.height)-s.y);
 const wx=F(F(width*v.getFloat32(0xe8,true))*F(height)),hy=F(F(h*v.getFloat32(0xe4,true))*F(height));
 const fullX=F(wx/1080),fullY=F(hy/1080);
 let halfX=F(wx/2160),halfY=F(hy/2160);
 let x=F(F(F(height)*v.getFloat32(0xc8,true))/480),y=F(F(F(height)*v.getFloat32(0xcc,true))/480);
 const anchor=flags&0x700;
 let left,right,top,bottom;
 if(anchor===0x100||anchor===0x400){left=x;right=F(x+fullX);}
 else if(anchor===0||anchor===0x300){left=F(x-halfX);right=F(x+halfX);}
 else {left=F(x-fullX);right=x;}
 if(anchor===0x300||anchor===0x400||anchor===0x500){top=y;bottom=F(y+fullY);}
 else {top=F(y-halfY);bottom=F(y+halfY);}
 const sourceX=cropped?F(v.getInt32(0x10c,true)):s.x,sourceY=cropped?F(v.getInt32(0x110,true)):s.y;
 const endX=cropped?F(sourceX+width):F(s.x+s.width),endY=cropped?F(sourceY+h):F(s.y+s.height);
 const u0=F(F(sourceX/resource.width)+v.getFloat32(0x2c,true)),u1=F(F(endX/resource.width)+v.getFloat32(0x2c,true));
 const v0=F(F(sourceY/resource.height)+v.getFloat32(0x30,true)),v1=F(F(endY/resource.height)+v.getFloat32(0x30,true));
 if(angle!==0){
  if(snap){halfX=rint(halfX);halfY=rint(halfY);x=rint(x);y=rint(y);}
  const sin=F(Math.sin(angle)),cos=F(Math.cos(angle));
  const xs=[-halfX,halfX,-halfX,halfX],ys=[-halfY,-halfY,halfY,halfY],out=new Float32Array(16);
  const offsetX=anchor===0x100||anchor===0x400?halfX:anchor===0||anchor===0x300?0:-halfX;
  const offsetY=anchor===0x300||anchor===0x400||anchor===0x500?halfY:0;
  for(let i=0;i<4;i++){
   let px=F(F(F(xs[i]*cos)+F(ys[i]*sin))+x),py=F(F(F(ys[i]*cos)-F(xs[i]*sin))+y);
   if(offsetX)px=F(px+offsetX);if(offsetY)py=F(py+offsetY);
   out.set([px,py,i&1?u1:u0,i&2?v1:v0],i*4);
  }
  return out;
 }
 if(snap){left=rint(left);right=rint(right);top=rint(top);bottom=rint(bottom);}
 return new Float32Array([left,top,u0,v0,right,top,u1,v0,left,bottom,u0,v1,right,bottom,u1,v1]);
}
