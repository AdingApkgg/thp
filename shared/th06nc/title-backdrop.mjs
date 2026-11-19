// Native helpers: request 0x140047080, update 0x140046ef0.
// Caller decides when to request a transition and whether to update/draw it.
const F=Math.fround;
export class TitleBackdrop {
 constructor(group){
  this.vms=[0x16170,0x16290,0x163b0,0x164d0,0x165f0,0x16710].map(p=>group.slots.get(p));
  if(this.vms.some(v=>!v))throw Error('TH06nc: incomplete backdrop animation group');
  this.control=new Uint8Array(0x28);this.v=new DataView(this.control.buffer);this.counter=0;
 }
 request(id){
  const v=this.v;
  if(id===2&&(v.getUint8(0)||this.vms.slice(2).some(vm=>vm.v.getInt16(0x86,true)>0||vm.v.getInt16(0x8c,true)>0)))id=5;
  this.counter=0;
  if([2,3,4,5,6].includes(id)){
   v.setUint8(0,1);v.setInt32(4,id===5?1:0,true);v.setInt32(8,0,true);
   v.setInt32(12,id===3?30:id===4?45:id===6?42:60,true);
   const target=id===3?F(0.5832):id===4?F(0.64395):F(0.6075),last=id===4?F(0.66825):target;
   for(let i=0;i<3;i++){
    v.setFloat32(16+i*4,this.vms[i+2].v.getFloat32(0xe4,true),true);
    v.setFloat32(28+i*4,i===2?last:target,true);
   }
  }else this.control.fill(0);
  for(const vm of this.vms.slice(2))vm.interrupt(id);
  return id;
 }
 tick(){
  for(const vm of this.vms)vm.tick();
  const v=this.v;if(!v.getUint8(0))return;
  const delay=v.getInt32(4,true);if(delay>0){v.setInt32(4,delay-1,true);return;}
  const elapsed=v.getInt32(8,true),duration=v.getInt32(12,true);
  const t=F(F(elapsed)/F(duration)),x=F(1-t),ratio=F(1-F(x*x));
  for(let i=0;i<3;i++){
   const start=v.getFloat32(16+i*4,true),target=v.getFloat32(28+i*4,true),scale=F(F(F(target-start)*ratio)+start);
   this.vms[i+2].v.setFloat32(0xe4,scale,true);this.vms[i+2].v.setFloat32(0xe8,scale,true);
  }
  if(elapsed>=duration)v.setUint8(0,0);else v.setInt32(8,elapsed+1,true);
 }
}
