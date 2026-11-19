import {applyAnmCommand} from './anm-command.mjs';
import {advanceAnmFrame} from './anm-frame.mjs';
// One ANM resource's scripts and sprites. Caller owns global RNG and external
// resource binding; sprite base is local here, before application table linking.
export class AnmVm {
 constructor(resource,id,{randomU16=null,spriteBase=0,resolveSprite=null,allowMissing=false}={}){
  this.resource=resource;this.randomU16=randomU16;this.spriteBase=spriteBase;this.resolveSprite=resolveSprite;
  this.script=resource.scripts.findLast(s=>s.id===id);
  if(!this.script&&!allowMissing)throw Error(`TH06nc ANM: missing script ${id}`);
  this.instructions=new Map((this.script?.instructions??[]).map(i=>[i.offset,i]));
  this.state=new Uint8Array(0x120);this.v=new DataView(this.state.buffer);
  for(const p of [0x3c,0x50,0x64,0x78,0xe4,0xe8])this.v.setFloat32(p,1,true);
  this.v.setUint32(0xec,0xffffffff,true);this.v.setUint32(0xc4,2,true);
  this.v.setInt32(0xb4,-999,true);this.v.setUint16(0x108,0xf0f,true);
  this.v.setUint16(0x38,id,true);
  this.pointer(0xf0,this.script?.offset??0);this.pointer(0xf8,this.script?.offset??0);
 }
 pointer(p,x){if(x!==undefined)this.v.setBigUint64(p,BigInt(x),true);return Number(this.v.getBigUint64(p,true));}
 interrupt(id){this.v.setInt16(0x8a,id,true);}
 get boundResource(){return this.boundBinding?this.boundBinding.resource:this._boundResource;}
 get boundSprite(){return this.boundBinding?this.boundBinding.sprite:this._boundSprite;}
 resolveInterrupt(){
  const v=this.v,pending=v.getInt16(0x8a,true);let found=null,fallback=null;
  for(const ins of this.script.instructions){
   if(ins.opcode===22){const label=new DataView(ins.args.buffer,ins.args.byteOffset,ins.args.byteLength).getInt32(0,true);if(label===pending){found=ins;break;}if(label===-1)fallback=ins;}
   if(ins.opcode===0||ins.opcode===15)break;
  }
  v.setInt16(0x8a,0,true);let flags=v.getUint32(0xc4,true)&~0x4000;
  v.setUint32(0xc4,flags,true);found??=fallback;
  if(!found){v.setInt32(0xb8,v.getInt32(0xb8,true)-1,true);return false;}
  const next=found.offset+4+found.args.length,ins=this.instructions.get(next);
  if(!ins)throw Error('TH06nc ANM: interrupt points outside script');
  this.pointer(0xf8,next);v.setInt32(0xb8,ins.time,true);v.setInt32(0xb4,-999,true);v.setUint32(0xc4,flags|1,true);return true;
 }
 bindSprite(id){
  const binding=this.resolveSprite?this.resolveSprite(id):null;
  if(this.resolveSprite&&(!binding||binding.active===false))return;
  const resource=binding?.resource??this.resource;
  const s=binding?.sprite??resource.sprites.findLast(s=>s.id===id);if(!s)return;
  this.boundBinding=binding;this._boundSprite=s;this._boundResource=resource;
  const v=this.v;
  this.pointer(0x100,id+1);v.setUint16(0x34,id,true);
  for(const p of [0x40,0x48,0x54,0x5c,0x68,0x70])v.setBigUint64(p,0n,true);
  for(const p of [0x64,0x78])v.setFloat32(p,1,true);
  const F=Math.fround;
  v.setFloat32(0x3c,F(F(F(s.x+s.width)-s.x)/resource.width),true);
  v.setFloat32(0x50,F(F(F(s.y+s.height)-s.y)/resource.height),true);
 }
 tick(){
  const v=this.v;if(!this.pointer(0xf8))return 1;
  let dispatch=true;
  if(v.getInt16(0x8a,true))dispatch=this.resolveInterrupt();
  let budget=100000;
  while(dispatch){
   if(--budget===0)throw Error('TH06nc ANM: non-yielding script');
   const ins=this.instructions.get(this.pointer(0xf8));if(!ins)throw Error('TH06nc ANM: invalid instruction pointer');
   if(ins.time>v.getInt32(0xb8,true))break;
   const action=applyAnmCommand(this.state,ins);
   if(action.exit){this.pointer(0xf8,0);return 1;}
   if(action.jump!==undefined){const offset=this.script.offset+action.jump,target=this.instructions.get(offset);if(!target)throw Error('TH06nc ANM: invalid jump');this.pointer(0xf8,offset);v.setInt32(0xb8,target.time,true);continue;}
   if(action.sprite){
    const a=new DataView(ins.args.buffer,ins.args.byteOffset,ins.args.byteLength);let id=a.getInt32(0,true);
    if(action.random){const range=a.getUint16(4,true);if(range){if(!this.randomU16)throw Error('TH06nc ANM: RNG not supplied');id+=this.randomU16()%range;}}
    v.setUint32(0xc4,v.getUint32(0xc4,true)|1,true);this.bindSprite(id+this.spriteBase);v.setInt32(0x90,v.getInt32(0xb8,true),true);
   }
   if(action.interruptWait){
    if(v.getInt16(0x8a,true)){dispatch=this.resolveInterrupt();continue;}
    v.setUint32(0xc4,v.getUint32(0xc4,true)|0x4000,true);v.setInt32(0xb8,v.getInt32(0xb8,true)-1,true);break;
   }
   this.pointer(0xf8,ins.offset+4+ins.args.length);
  }
  advanceAnmFrame(this.state);return 0;
 }
}
