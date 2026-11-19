const F=Math.fround,epsilon=F(1e-6);
function normalized(values){
 let sum=F(F(values[1]*values[1])+F(values[0]*values[0]));for(let i=2;i<values.length;i++)sum=F(sum+F(values[i]*values[i]));
 const length=F(Math.sqrt(sum));if(epsilon>=Math.abs(length))return values.length===4?[0,0,0,1]:[0,0,0];const inverse=F(1/length);return values.map(x=>F(inverse*x));
}
// Matrix helper 568c0 normalizes the quaternion before computing the rotation.
function rotationMatrix(quaternion){
 const [x,y,z,w]=normalized(quaternion),xx=F(F(x+x)*x),yy=F(F(y+y)*y),zz=F(F(z+z)*z),xy=F(F(x+x)*y),xz=F(F(x+x)*z),yz=F(F(y+y)*z),wx=F(F(w+w)*x),wy=F(F(w+w)*y),wz=F(F(w+w)*z);
 return [F(1-F(zz+yy)),F(wz+xy),F(xz-wy),0,F(xy-wz),F(1-F(zz+xx)),F(wx+yz),0,F(wy+xz),F(yz-wx),F(1-F(yy+xx)),0,0,0,0,1];
}
// Orbit callback 2aae0, used by the three boss halo effect kinds.
export function advanceOrbitEffect(effect,{sin=Math.sin,cos=Math.cos}={}){
 const {v}=effect,axis=normalized(Array.from({length:3},(_,i)=>v.getFloat32(0x18+i*4,true))),angle=v.getFloat32(0x2c,true),sine=F(sin(angle)),quaternion=[...axis.map(x=>F(sine*x)),F(cos(angle))];
 quaternion.forEach((x,i)=>v.setFloat32(0x160+i*4,x,true));const matrix=rotationMatrix(quaternion);
 const cross=[F(axis[1]-F(axis[2]*0)),F(F(axis[2]*0)-axis[0]),F(F(axis[0]*0)-F(axis[1]*0))];
 const sum=F(F(F(cross[1]*cross[1])+F(cross[0]*cross[0]))+F(cross[2]*cross[2]));
 const normal=F(1e-5)>sum?cross:normalized(cross),strength=v.getFloat32(0x184,true),vector=normal.map(x=>F(strength*x));
 const transformed=Array.from({length:4},(_,i)=>F(F(F(F(vector[1]*matrix[4+i])+F(vector[0]*matrix[i]))+F(vector[2]*matrix[8+i]))+matrix[12+i]));
 if(!(epsilon>=Math.abs(transformed[3]))){const inverse=F(1/transformed[3]);for(let i=0;i<3;i++)transformed[i]=F(inverse*transformed[i]);}
 v.setFloat32(0x174,F(transformed[0]+v.getFloat32(0x30,true)),true);v.setFloat32(0x178,F(transformed[1]+v.getFloat32(0x34,true)),true);v.setFloat32(0x17c,F(F(transformed[2]*F(6))+v.getFloat32(0x38,true)),true);
 if(v.getUint8(0x180)){
  const frame=(v.getUint8(0x3c)+1)&255;v.setUint8(0x3c,frame);const signed=(frame<<24)>>24;if(signed>=16)return 0;
  const opacity=F(F(1)-F(F(signed)*F(0.0625))),alpha=Math.trunc(F(opacity*F(255)))|0;
  v.setUint32(0x12c,(v.getUint32(0x12c,true)&0xffffff)|(alpha<<24),true);const scale=F(F(2)-opacity);v.setFloat32(0x124,scale,true);v.setFloat32(0x128,scale,true);
 }
 return 1;
}
