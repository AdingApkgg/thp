const f=Math.fround,epsilon=f(1e-6);
// Unaccepted transcription of the observed D3D9 SWVP clip-vertex path.
// Source vertices outside an active Z plane retain homogeneous coordinates.
// Vertices inside Z are reconstructed from their rounded screen packet even
// when outside X/Y; those X/Y vertices then require screen reprojection.
export function clipTrianglesToWindow(records,type,viewport,snap=x=>x){
 const[x,y,width,height,min,max]=viewport,w=f(width),h=f(height),depth=f(max-min),biasX=f(f(x)+epsilon),biasY=f(f(f(y)+h)+epsilon),inverseX=f(1/w),inverseY=f(1/-h),inverseZ=f(1/depth);
 const input=records.map(v=>{const c=v.clip,p=v.window||v.position||v.packet.slice(0,4),outside=c[0]<-c[3]||c[0]>c[3]||c[1]<-c[3]||c[1]>c[3]||c[2]<0||c[2]>c[3];let clip;
  if(c[2]<0||c[2]>c[3])clip=[f(f(c[0]+c[3])*.5),f(f(c[1]+c[3])*.5),c[2],c[3]];
  else{const rw=f(1/p[3]);clip=[f(f(f(p[0]-biasX)*rw)*inverseX),f(f(f(p[1]-biasY)*rw)*inverseY),f(f(f(p[2]-min)*rw)*inverseZ),rw];}
  return{...v,clip,reproject:outside,near:c[2]<0,far:c[2]>c[3]};
 });
 const triangles=[];if(type===4){for(let i=0;i<input.length;i+=3)triangles.push(input.slice(i,i+3));}else if(type===5){for(let i=0;i+2<input.length;i++)triangles.push(i&1?[input[i],input[i+2],input[i+1]]:input.slice(i,i+3));}else if(type===6){for(let i=1;i+1<input.length;i++)triangles.push([input[0],input[i],input[i+1]]);}else return null;
 const output=[];
 for(const triangle of triangles){let polygon=triangle;const active=[triangle.some(v=>v.near),triangle.some(v=>v.far)];
  for(let plane=0;plane<2;plane++){
   if(!active[plane])continue;const far=plane===1,distance=v=>far?f(v.clip[3]-v.clip[2]):v.clip[2],next=[];
   for(let i=0;i<polygon.length;i++){
    let a=polygon[(i+polygon.length-1)%polygon.length],b=polygon[i],da=distance(a),db=distance(b);const ia=da>=0,ib=db>=0;if(ia)next.push(a);
    if(ia!==ib){if(!ia){[a,b]=[b,a];[da,db]=[db,da];}const t=f(da/f(da-db)),mix=(a,b)=>f(a+f(t*f(b-a)));next.push({clip:a.clip.map((v,j)=>mix(v,b.clip[j])),attributes:a.attributes.map((v,j)=>mix(v,b.attributes[j])),generated:true});}
   }
   polygon=next;if(polygon.length<3)break;
  }
  for(let i=1;i+1<polygon.length;i++)for(const v of[polygon[0],polygon[i],polygon[i+1]]){
   if(!v.generated&&!v.reproject){output.push(...v.packet);continue;}
   const c=v.clip,q=f(1/c[3]),position=[snap(f(f(f(c[0]*w)*q)+biasX)),snap(f(f(f(c[1]*-h)*q)+biasY)),f(f(f(q*c[2])*depth)+min),q];output.push(...position,...v.attributes,position[2]);
  }
 }
 return Float32Array.from(output);
}
