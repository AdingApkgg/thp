const f=Math.fround;
// CPU selects topology; the vertex shader evaluates each generated edge.
// Records carry homogeneous positions and RGBA/UV/fog attributes only.
export function buildHardwareClipGeometry(records,type,far){
 const triangles=[];
 if(type===4){for(let i=0;i<records.length;i+=3)triangles.push(records.slice(i,i+3));}
 else if(type===5){for(let i=0;i+2<records.length;i++)triangles.push(i&1?[records[i+1],records[i],records[i+2]]:records.slice(i,i+3));}
 else if(type===6){for(let i=1;i+1<records.length;i++)triangles.push([records[0],records[i],records[i+1]]);}
 else return null;
 const output=[],distance=v=>far?f(v.clip[3]-v.clip[2]):v.clip[2];
 const emit=v=>output.push(...v.a.clip,...v.b.clip,...v.a.attributes.slice(0,4),...v.b.attributes.slice(0,4),...v.a.attributes.slice(4,7),...v.b.attributes.slice(4,7),v.generated,far?1:0);
 for(const triangle of triangles){const polygon=[];
  for(let i=0;i<3;i++){
   const a=triangle[i],b=triangle[(i+1)%3],ia=distance(a)>=0,ib=distance(b)>=0;
   if(ia)polygon.push({a,b:a,generated:0});
   if(ia!==ib)polygon.push({a,b,generated:1});
  }
  if(polygon.length===4&&(!far||triangle.findIndex(v=>distance(v)<0)!==1))polygon.push(polygon.shift());
  for(let i=1;i+1<polygon.length;i++){emit(polygon[0]);emit(polygon[i]);emit(polygon[i+1]);}
 }
 return Float32Array.from(output);
}
