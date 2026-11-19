const F=Math.fround;
// Left-handed look-at implementation 56af0, including its float32 norm and
// small-vector threshold. Camera setup 3bc10 uses logical viewport dimensions.
export function lookAtLeftHanded(eye,target,up=[0,1,0]){
 const normalize=a=>{const length=F(Math.sqrt(F(F(F(a[1]*a[1])+F(a[0]*a[0]))+F(a[2]*a[2]))));if(Math.abs(length)<=F(1e-6))return [0,0,0];const inverse=F(1/length);return a.map(n=>F(n*inverse));},cross=(a,b)=>[F(F(a[1]*b[2])-F(a[2]*b[1])),F(F(a[2]*b[0])-F(a[0]*b[2])),F(F(a[0]*b[1])-F(a[1]*b[0]))];
 const z=normalize(target.map((n,k)=>F(n-eye[k]))),x=normalize(cross(up,z)),y=cross(z,x),dot=(a,reverse=false)=>-F(F(F(a[reverse?1:0]*eye[reverse?1:0])+F(a[reverse?0:1]*eye[reverse?0:1]))+F(a[2]*eye[2]));
 return new Float32Array([x[0],y[0],z[0],0,x[1],y[1],z[1],0,x[2],y[2],z[2],0,dot(x,true),dot(y),dot(z,true),1]);
}
export function createStdCamera({width=384,height=448,direction=[0,0,1],depthOffset=0,tan=Math.tan}={}){
 const halfWidth=F(F(width)*F(.5)),halfHeight=F(F(height)*F(.5)),angle=F(Math.PI/12),distance=F(halfHeight/F(tan(angle))),eye=[halfWidth,F(-halfHeight),F(F(-distance)*F(direction[2]))],target=[F(halfWidth+F(direction[0])),F(F(direction[1])-halfHeight),0],view=lookAtLeftHanded(eye,target),far=F(F(depthOffset)+F(10000)),denominator=F(far-F(100)),focal=F(1/F(tan(angle))),aspect=F(F(width)/F(height)),projection=new Float32Array([F(focal/aspect),0,0,0,0,focal,0,0,0,0,F(far/denominator),1,0,0,F(F(-F(far*F(100)))/denominator),0]);
 return {view,projection,distance:Math.abs(distance)};
}
