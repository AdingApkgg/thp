const F=Math.fround;
// Uncropped world draw (4dc0): ANM UV matrix transforms the manager's
// 256-unit square, unlike the pixel-sized 2D draw path (67f0).
export function anmWorldQuad(vm,{sin=Math.sin,cos=Math.cos}={}){
 const v=vm.v,flags=v.getUint32(0xc4,true),resource=vm.boundResource??vm.resource;
 if(vm.boundBinding?.active===false||(flags&3)!==3||!v.getUint32(0xec,true)||!vm.pointer(0x100))return null;
 if(v.getInt32(0x114,true)>0)throw Error('TH06nc: cropped world quad not yet implemented');
 const sprite=vm.boundSprite??resource.sprites.findLast(s=>s.id===v.getUint16(0x34,true));if(!sprite)return null;
 let matrix=Array.from({length:16},(_,i)=>v.getFloat32(0x3c+i*4,true));
 matrix[0]=F(matrix[0]*v.getFloat32(0xe8,true));matrix[5]=F(matrix[5]*-v.getFloat32(0xe4,true));
 for(let axis=0;axis<3;axis++){
  const angle=v.getFloat32(0x9c+axis*4,true);if(angle===0)continue;
  const c=F(cos(angle)),s=F(sin(angle)),rotation=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1];
  if(axis===0){rotation[5]=c;rotation[6]=s;rotation[9]=-s;rotation[10]=c;}
  else if(axis===1){rotation[0]=c;rotation[2]=-s;rotation[8]=s;rotation[10]=c;}
  else{rotation[0]=c;rotation[1]=s;rotation[4]=-s;rotation[5]=c;}
  const next=[];for(let row=0;row<4;row++)for(let col=0;col<4;col++){let sum=0;for(let k=0;k<4;k++)sum=F(sum+F(matrix[row*4+k]*rotation[k*4+col]));next[row*4+col]=sum;}matrix=next;
 }
 const width=F(F(sprite.x+sprite.width)-sprite.x),height=F(F(sprite.y+sprite.height)-sprite.y),anchor=flags&0x700;
 let x=v.getFloat32(0xc8,true),y=-v.getFloat32(0xcc,true),z=v.getFloat32(0xd0,true);
 const fullWidth=F(width*v.getFloat32(0xe8,true)),halfHeight=F(F(height*v.getFloat32(0xe4,true))*F(0.5));
 if(anchor===0x100||anchor===0x400)x=F(x+Math.abs(F(fullWidth*F(0.5))));
 else if(anchor!==0&&anchor!==0x300)x=F(x+Math.abs(fullWidth));
 if(anchor===0x300||anchor===0x400||anchor===0x500)y=F(y-Math.abs(halfHeight));
 const out=new Float32Array(20);
 for(let i=0;i<4;i++){
  const a=i&1?128:-128,b=i&2?128:-128;
  for(let col=0;col<3;col++)out[i*5+col]=F(F(F(F(matrix[col]*a)+F(matrix[4+col]*b))+F(matrix[8+col]*0))+[x,y,z][col]);
  out[i*5+3]=F(F(F(v.getFloat32(0x3c,true)*(i&1?1:0))+F(sprite.x/resource.width))+v.getFloat32(0x2c,true));
  out[i*5+4]=F(F(F(v.getFloat32(0x50,true)*(i&2?1:0))+F(sprite.y/resource.height))+v.getFloat32(0x30,true));
 }
 return out;
}

// Flat gameplay plane only. Perspective/STD scenes need their own camera.
export function projectFlatWorldQuad(quad,height=1080){
 if(!quad)return null;const out=new Float32Array(16);
 for(let i=0;i<4;i++){
  if(quad[i*5+2]!==0)throw Error('TH06nc: non-planar world quad needs a camera');
  out.set([F(F(quad[i*5]*F(height))/480),F(F(-quad[i*5+1]*F(height))/480),quad[i*5+3],quad[i*5+4]],i*4);
 }
 return out;
}
