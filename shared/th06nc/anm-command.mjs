// Native-layout state for the TH06nc ANM VM (0x120 bytes).
// Command writes reconstructed from switch 0x140006a4b. Frame integration,
// sprite binding, RNG, jumps and interrupts are owned by the VM scheduler.
const sizes=[0,4,8,4,4,4,0,0,0,12,12,8,8,0,0,0,8,12,16,16,16,0,4,0,0,4,4,4,4,4,12,4,0,0,0,0];
export function applyAnmCommand(state,ins){
 if(!(state instanceof Uint8Array)||state.length!==0x120)throw Error('TH06nc ANM: invalid VM state');
 if(ins.args.length!==sizes[ins.opcode])throw Error(`TH06nc ANM: invalid command ${ins.opcode}`);
 const v=new DataView(state.buffer,state.byteOffset,state.byteLength),a=new DataView(ins.args.buffer,ins.args.byteOffset,ins.args.byteLength);
 const u=p=>v.getUint32(p,true),put=(p,x)=>v.setUint32(p,x,true),arg=p=>a.getUint32(p,true);
 const word=(p,x)=>v.setUint16(p,x,true),flag=(mask,value)=>put(0xc4,(u(0xc4)&~mask)|(value&mask));
 const copy=(dest,n)=>{for(let i=0;i<n;i+=4)put(dest+i,arg(i));};
 const timer=p=>{put(p,-999);put(p+4,0);};
 switch(ins.opcode){
 case 0:flag(1,0);return {exit:true};
 case 15:return {exit:true};
 case 1:case 16:return {sprite:true,random:ins.opcode===16};
 case 5:return {jump:arg(0)};
 case 21:case 24:
  if(ins.opcode===24)flag(1,0);
  return {interruptWait:true};
 case 2:put(0xe8,arg(0));put(0xe4,arg(4));break;
 case 3:put(0xec,(u(0xec)&0xffffff)|((arg(0)&255)<<24));break;
 case 4:put(0xec,(u(0xec)&0xff000000)|(arg(0)&0xffffff));break;
 case 7:case 8:{const bit=ins.opcode===7?0x40:0x80,p=ins.opcode===7?0xe8:0xe4;put(0xc4,u(0xc4)^bit);v.setFloat32(p,-v.getFloat32(p,true),true);break;}
 case 9:copy(0x9c,12);break;
 case 10:copy(0xa8,12);break;
 case 11:put(0x80,arg(0));put(0x7c,arg(4));word(0x86,0);break;
 case 12:put(0xbc,u(0xec));put(0xc0,(u(0xec)&0xffffff)|(arg(0)<<24));word(0x84,a.getUint16(4,true));timer(0x94);break;
 case 13:flag(4,4);break;
 case 14:flag(4,0);break;
 case 17:copy(u(0xc4)&32?0x18:0xc8,12);break;
 case 18:case 19:case 20:{
  flag(0x1800,ins.opcode===19?0x800:ins.opcode===20?0x1000:0);
  const p=u(0xc4)&32?0x18:0xc8;
  for(let i=0;i<12;i+=4)put(i,u(p+i));
  copy(12,12);word(0x8c,a.getUint16(12,true));timer(0x24);break;
 }
 case 23:flag(0x700,0x400);break;
 case 25:flag(32,arg(0)<<5);break;
 case 26:word(0x88,a.getUint16(0,true));break;
 case 27:case 28:{const p=ins.opcode===27?0x2c:0x30;let x=Math.fround(v.getFloat32(p,true)+a.getFloat32(0,true));if(x>=1)x=Math.fround(x-1);else if(x<0)x=Math.fround(x+1);v.setFloat32(p,x,true);break;}
 case 29:flag(1,arg(0));break;
 case 30:put(0x80,arg(0));put(0x7c,arg(4));word(0x86,a.getUint16(8,true));timer(0xdc);put(0xd8,u(0xe8));put(0xd4,u(0xe4));break;
 case 31:flag(0x2000,arg(0)<<13);break;
 case 32:flag(0x700,0x300);break;
 case 33:flag(0x700,0x100);break;
 case 34:flag(0x700,0x500);break;
 case 35:flag(0x700,0x200);break;
 case 6:case 22:break;
 default:throw Error(`TH06nc ANM: unsupported command ${ins.opcode}`);
 }
 return {advance:true};
}
