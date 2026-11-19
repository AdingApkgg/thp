const F=Math.fround;
const localOffsets=new Map(Array.from({length:8},(_,i)=>[-10001-i,0x48+i*4]).concat(Array.from({length:4},(_,i)=>[-10009-i,0x70+i*4]),[[-10015,0xb0],[-10016,0xb4],[-10017,0xb8],[-10022,4],[-10024,0x234],[-10101,0x68]]));
const computedIds=new Set([-10013,-10018,-10019,-10020,-10021,-10023,-10025,-10100]);
const asView=bytes=>new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);
const bitcast=new DataView(new ArrayBuffer(4));
// Float-source resolver 0x14002e260. Raw integer and assignment helpers are separate.
export class EclOperands {
 constructor(enemy,{difficulty=0,rank=0,playerPosition=[0,0,0],character=0,shot=0,rng=null,atan2=null}={}){
  this.enemy=enemy;this.v=asView(enemy);this.environment={difficulty,rank,playerPosition,character,shot,rng,atan2};
  this.scratch=new Uint8Array(12);this.scratchView=asView(this.scratch);
 }
 float(value){
  const id=Number.isFinite(value)&&value>=-2147483648&&value<2147483648?Math.trunc(value):-2147483648;
  if(localOffsets.has(id))return this.v.getFloat32(localOffsets.get(id),true);
  const env=this.environment,s=this.scratchView;
  if(id===-10013){bitcast.setInt32(0,env.difficulty,true);return bitcast.getFloat32(0,true);}
  if(id<=-10018&&id>=-10020)return F(env.playerPosition[-10018-id]);
  if(id===-10021){
   const dx=F(F(env.playerPosition[0])-this.v.getFloat32(0xb0,true)),dy=F(F(env.playerPosition[1])-this.v.getFloat32(0xb4,true));
   if(dx===0&&dy===0)s.setFloat32(0,F(Math.PI/2),true);
   else{if(!env.atan2)throw Error('TH06nc ECL: angle operand needs the shared atan2 service');s.setFloat32(0,env.atan2(dy,dx),true);}
   return s.getFloat32(0,true);
  }
  if(id===-10023){
   const delta=Array.from({length:3},(_,i)=>F(F(env.playerPosition[i])-this.v.getFloat32(0xb0+i*4,true)));
   const sum=F(F(F(delta[1]*delta[1])+F(delta[0]*delta[0]))+F(delta[2]*delta[2]));
   s.setFloat32(4,F(Math.sqrt(sum)),true);return s.getFloat32(4,true);
  }
  if(id===-10025){s.setInt32(8,(env.shot&255)+(env.character&255)*2,true);return s.getFloat32(8,true);}
  if(id===-10100){if(!env.rng)throw Error('TH06nc ECL: random operand needs the shared RNG');this.v.setFloat32(0x6c,env.rng.angle(),true);return this.v.getFloat32(0x6c,true);}
  return value;
 }
 // Integer-source operands and assignment encode IDs as raw signed i32 words.
 bits(raw){
  const id=raw|0;if(localOffsets.has(id))return this.v.getUint32(localOffsets.get(id),true);
  if(computedIds.has(id)){const value=this.float(id);bitcast.setFloat32(0,value,true);return bitcast.getUint32(0,true);}
  return raw>>>0;
 }
 integer(raw){return this.bits(raw)|0;}
 // 18/19 adjust the referenced word, including float variables' raw bits.
 // Unrecognized destinations instead refer to the instruction's own argument.
 increment(destination,delta,shared=this.environment){
  const offset=localOffsets.get(destination);if(offset!==undefined){this.v.setUint32(offset,(this.v.getUint32(offset,true)+delta)>>>0,true);return true;}
  const env=this.environment;if(destination===-10013){env.difficulty=((env.difficulty|0)+delta)|0;shared.difficulty=env.difficulty;return true;}
  if(destination<=-10018&&destination>=-10020){const axis=-10018-destination;bitcast.setFloat32(0,env.playerPosition[axis],true);bitcast.setUint32(0,(bitcast.getUint32(0,true)+delta)>>>0,true);env.playerPosition[axis]=bitcast.getFloat32(0,true);if(shared.playerPosition)shared.playerPosition[axis]=env.playerPosition[axis];return true;}
  if([-10021,-10023,-10025,-10100].includes(destination)){this.float(destination);const view=destination===-10100?this.v:this.scratchView,p=destination===-10100?0x6c:destination===-10021?0:destination===-10023?4:8;view.setUint32(p,(view.getUint32(p,true)+delta)>>>0,true);return true;}
  return false;
 }
 // 25 computes atan2(y2-y1,x2-x1) into a float destination. All four
 // references resolve first, preserving shared scratch/RNG aliasing.
 angleBetween(destination,coordinates,atan2=this.environment.atan2){
  if([-10021,-10023,-10025,-10100].includes(destination)){this.float(destination);return;}
  const offset=localOffsets.get(destination);if(![0x58,0x5c,0x60,0x64,0xb0,0xb4,0xb8,0x68].includes(offset))return;
  if(!atan2)throw Error('TH06nc ECL: angle command requires atan2');
  const refs=coordinates.map(raw=>this.reference(raw,{floating:true})),values=refs.map(ref=>{bitcast.setUint32(0,ref(),true);return bitcast.getFloat32(0,true);});
  this.v.setFloat32(offset,F(atan2(F(values[3]-values[1]),F(values[2]-values[0]))),true);
 }
 // 26 reads a raw-ID reference, normalizes with the native iteration guard,
 // then uses the ordinary assignment helper (including its side effects).
 normalizeAngle(destination){
  const source=this.reference(destination>>>0);bitcast.setUint32(0,source(),true);let value=F(bitcast.getFloat32(0,true)+F(0)),iterations=0;
  while(value>F(Math.PI)){value=F(value+F(-2*Math.PI));if(iterations++>16)break;}
  while(value<F(-Math.PI)){value=F(value+F(2*Math.PI));if(iterations++>16)break;}
  bitcast.setFloat32(0,value,true);this.assign(destination,bitcast.getUint32(0,true));
 }
 reference(raw,{floating=false}={}){
  raw>>>=0;bitcast.setUint32(0,raw,true);const value=floating?bitcast.getFloat32(0,true):raw|0;
  const id=Number.isFinite(value)&&value>=-2147483648&&value<2147483648?Math.trunc(value):-2147483648;
  const local=localOffsets.get(id);
  if(local!==undefined)return ()=>this.v.getUint32(local,true);
  if(computedIds.has(id)){
   this.float(id);
   if(id===-10100)return ()=>this.v.getUint32(0x6c,true);
   if(id===-10021)return ()=>this.scratchView.getUint32(0,true);
   if(id===-10023)return ()=>this.scratchView.getUint32(4,true);
   if(id===-10025)return ()=>this.scratchView.getUint32(8,true);
   if(id===-10013)return ()=>this.environment.difficulty>>>0;
   return ()=>{bitcast.setFloat32(0,this.environment.playerPosition[-10018-id],true);return bitcast.getUint32(0,true);};
  }
  return ()=>raw;
 }
 arithmetic(destination,left,right,operation){
  // Multiplication has an extra original prepass over raw integer source IDs.
  if(operation==='mul'){this.reference(left);this.reference(right);}
  const offset=localOffsets.get(destination),special=destination===-10025;
  if([-10021,-10023,-10100].includes(destination)){this.float(destination);return;}
  if(offset===undefined&&!special)return;
  if(special)this.float(destination);
  const floating=(offset>=0x58&&offset<=0x64)||[0xb0,0xb4,0xb8,0x68].includes(offset);
  const lhs=this.reference(left,{floating}),rhs=this.reference(right,{floating});
  let x=lhs(),y=rhs(),result;
  if(floating){bitcast.setUint32(0,x,true);x=bitcast.getFloat32(0,true);bitcast.setUint32(0,y,true);y=bitcast.getFloat32(0,true);result=F(operation==='add'?x+y:operation==='sub'?x-y:operation==='mul'?x*y:operation==='div'?x/y:x%y);}
  else{
   x|=0;y|=0;if(['div','mod'].includes(operation)&&(y===0||(x===-2147483648&&y===-1)))throw Error('TH06nc ECL: native integer division fault');
   result=operation==='add'?(x+y)|0:operation==='sub'?(x-y)|0:operation==='mul'?Math.imul(x,y):operation==='div'?Math.trunc(x/y):x%y;
  }
  const target=special?this.scratchView:this.v,p=special?8:offset;
  if(floating){if(Number.isNaN(result))target.setUint32(p,0xffc00000,true);else target.setFloat32(p,result,true);}else target.setInt32(p,result,true);
 }
 // Assignment helper 0x14002e620, shared by ECL opcodes 4 and 5.
 assign(destination,sourceBits){
  const bits=this.bits(sourceBits),offset=localOffsets.get(destination);
  if(offset!==undefined){this.v.setUint32(offset,bits,true);return;}
  if([-10021,-10023,-10100].includes(destination)){this.float(destination);return;}
  if(destination===-10025){this.float(destination);this.scratchView.setUint32(8,bits,true);}
 }
}
