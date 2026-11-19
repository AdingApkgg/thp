// Post-command phase of native ANM update, 0x140006e0a..0x140007470.
// Native animation updates advance by one tick, without host delta-time scaling.
const F=Math.fround,PI=F(Math.PI),TAU=F(2*Math.PI);
export function advanceAnmFrame(state){
 if(!(state instanceof Uint8Array)||state.length!==0x120)throw Error('TH06nc ANM: invalid VM state');
 const v=new DataView(state.buffer,state.byteOffset,state.byteLength);
 const f=p=>v.getFloat32(p,true),put=(p,x)=>v.setFloat32(p,x,true),i=p=>v.getInt32(p,true),int=(p,x)=>v.setInt32(p,x,true),short=p=>v.getInt16(p,true),word=(p,x)=>v.setInt16(p,x,true);
 const flags=v.getUint32(0xc4,true);
 for(let p=0x9c;p<=0xa4;p+=4){
  const velocity=f(p+12);if(velocity===0)continue;
  let x=F(f(p)+velocity),count=0;
  while(x>PI){x=F(x-TAU);if(count++>16)break;}
  while(x< -PI){x=F(x+TAU);if(count++>16)break;}
  put(p,x);
 }
 let duration=short(0x86);
 if(duration>0){
  const t=(i(0xe0)+1)|0;int(0xdc,i(0xe0));int(0xe0,t);
  let x=f(0x80),y=f(0x7c);
  if(t>=duration){word(0x86,0);v.setBigUint64(0x7c,0n,true);}
  else {x=F(F(F(F(x-f(0xd8))*F(t))/F(duration))+f(0xd8));y=F(F(F(F(y-f(0xd4))*F(t))/F(duration))+f(0xd4));}
  put(0xe8,flags&64?F(-x):x);put(0xe4,flags&128?F(-y):y);
 }else{put(0xe4,F(f(0xe4)+f(0x7c)));put(0xe8,F(f(0xe8)+f(0x80)));}
 duration=short(0x84);
 if(duration>0){
  const t=(i(0x98)+1)|0;int(0x94,i(0x98));int(0x98,t);
  const ratio=Math.min(1,F(F(t)/F(duration)));
  for(let j=0;j<4;j++){
   const a=v.getUint8(0xbc+j),b=v.getUint8(0xc0+j);
   v.setUint8(0xec+j,Math.max(0,Math.min(255,Math.trunc(F(F((b-a)*ratio)+a)))));
  }
  if(t>=duration)word(0x84,0);
 }
 duration=short(0x8c);
 if(duration!==0){
  const t=i(0x28);let ratio=Math.min(1,F(F(t)/F(duration)));
  const mode=(flags>>>11)&3;
  if(mode===1){const x=F(1-ratio);ratio=F(1-F(x*x));}
  if(mode===2){const x=F(1-ratio);ratio=F(1-F(F(F(x*x)*x)*x));}
  const rest=F(1-ratio),p=flags&32?0x18:0xc8;
  for(let j=0;j<12;j+=4)put(p+j,F(F(rest*f(j))+F(ratio*f(12+j))));
  if(t>=duration)word(0x8c,0);
  int(0x28,t+1);int(0x24,t);
 }
 int(0xb4,i(0xb8));int(0xb8,i(0xb8)+1);
}
