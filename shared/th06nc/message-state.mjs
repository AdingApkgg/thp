import {openMessage} from './message-open.mjs';
import {rebindAnm} from './anm-rebind.mjs';
import {advanceMessage} from './message-update.mjs';
export class MessageState {
 constructor(program,{anmBank,environment={},storage=null}={}){this.program=program;this.anmBank=anmBank;this.environment=environment;this.bytes=storage??new Uint8Array(0x4000);if(!(this.bytes instanceof Uint8Array)||this.bytes.length<0x4000)throw Error('TH06nc message: owner storage too small');this.v=new DataView(this.bytes.buffer,this.bytes.byteOffset,this.bytes.byteLength);this.anms=new Map();this.v.setInt32(0x36b0,-1,true);this.v.setBigUint64(0x38f8,1n,true);this.v.setBigUint64(0x3b58,1n,true);this.instructions=new Map(program.uniqueScripts.flatMap(s=>s.instructions.map(i=>[i.offset,i])));}
 open(id,services={}){const opened=openMessage(this,id,{environment:this.environment,...services});if(opened)this.anms.clear();return opened;}
 vm(offset){
  if(!this.anms.has(offset)){const bytes=this.bytes.subarray(offset,offset+288),vm=this.anmBank.createVm(this.v.getUint16(offset+0x38,true),{allowMissing:true,randomU16:this.environment.rng?()=>this.environment.rng.next16():null});vm.resolveSprite=id=>this.anmBank.sprites.get(id);vm.state=bytes;vm.v=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);const sprite=Number(vm.v.getBigUint64(0x100,true));vm.boundBinding=sprite?this.anmBank.sprites.get(sprite-1):undefined;this.anms.set(offset,vm);}return this.anms.get(offset);
 }
 rebind(offset,id){const vm=rebindAnm(this.anmBank,id,this.bytes.subarray(offset,offset+288),{randomU16:this.environment.rng?()=>this.environment.rng.next16():null});this.anms.set(offset,vm);return vm;}
 tick(input=0,services={}){return advanceMessage(this,{input,...services});}
}
