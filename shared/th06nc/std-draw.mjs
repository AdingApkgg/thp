import {identityMatrix,multiplyMatrix,transformCoordinate} from './matrix.mjs';
const F=Math.fround;
// The original 78cb0 performs its visibility test on projected Y only.
// Preserve its eight-corner order and all per-instance mutations of shared VMs.
export function drawStdLayer(state,layer,draw,{view,projection,viewport,setTextureFactor=null}={}){
 if(!view||!projection||!viewport)throw Error('TH06nc STD: camera matrices and viewport required');
 const {program,v}=state,file=new DataView(state.bytes.buffer,state.bytes.byteOffset,state.bytes.byteLength),camera=Array.from({length:3},(_,k)=>v.getFloat32(0xc0+k*4,true)),screen=p=>[F(F(F(F(p[0]+1)*F(viewport.width))*F(.5))+F(viewport.x)),F(F(F(F(1-p[1])*F(viewport.height))*F(.5))+F(viewport.y)),F(F(F(F(viewport.maxZ)-F(viewport.minZ))*p[2])+F(viewport.minZ))];
 const project=p=>{const translation=identityMatrix();translation.set(p,12);return transformCoordinate([0,0,0],multiplyMatrix(multiplyMatrix(multiplyMatrix(identityMatrix(),translation),view),projection));};
 setTextureFactor?.({stage:1,operation:1,color:0xffffffff});let calls=0;
 for(const instance of program.instances){const object=program.objects[instance.objectIndex],objectLayer=file.getInt8(object.offset+2);if(objectLayer!==layer)continue;
  const x=F(F(F(instance.position[0])+F(object.position[0]))-camera[0]),y=F(-F(F(F(instance.position[1])+F(object.position[1]))-camera[1])),z=F(F(F(F(instance.position[2])+F(object.position[2]))-camera[2])+F(object.size[2])),x1=F(x+F(object.size[0])),y1=F(y-F(object.size[1])),z0=F(z-F(object.size[2]));
  const corners=[[x,y,z],[x,y1,z],[x,y1,z0],[x,y,z0],[x1,y,z],[x1,y1,z],[x1,y1,z0],[x1,y,z0]];
  if(!corners.some(p=>{const sy=screen(project(p))[1];return sy>=viewport.y&&sy<=viewport.y+viewport.height;}))continue;
  for(const face of object.primitives){if(face.type!==0)continue;const index=file.getInt16(face.offset+6,true),vm=state.vms[index],a=vm.v,position=face.position.map((n,k)=>F(F(F(n)+F(instance.position[k]))-camera[k]));position.forEach((n,k)=>a.setFloat32(0xc8+k*4,n,true));const sprite=vm.boundSprite;
   if(face.size[0]!==0)a.setFloat32(0xe8,F(face.size[0]/sprite.width),true);if(face.size[1]!==0)a.setFloat32(0xe4,F(face.size[1]/sprite.height),true);
   let space='world';if(a.getInt16(0x88,true)===2){space='screen';const width=face.size[0]===0?sprite.width:face.size[0],p=[position[0],F(-position[1]),position[2]],first=screen(project(p)),depth=first[2];p[0]=F(p[0]+F(width*a.getFloat32(0xe8,true)));const last=screen(project(p)),scale=F(F(F(F(last[0]-first[0])/width)*F(1080))/F(480));a.setFloat32(0xe8,scale,true);a.setFloat32(0xe4,scale,true);a.setFloat32(0xc8,first[0],true);a.setFloat32(0xcc,first[1],true);a.setFloat32(0xd0,depth,true);}
   draw(vm,{space,instance,object,face,index,layer});calls++;
  }
 }
 setTextureFactor?.({stage:3,operation:3,color:0xffffffff});return calls;
}
