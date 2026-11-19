import {AnmBank} from './anm-bank.mjs';
import {rebindAnm} from './anm-rebind.mjs';
const emptyBank=new AnmBank();
export const musicRoomAssets=Object.freeze([
 ['music.anm',69,0x7d5],['music00.anm',46,0x100],['music01.anm',47,0x101],['music02.anm',48,0x111],
].map(([file,slot,base])=>Object.freeze({archive:'th06TL.dat',file,slot,base})));
export class MusicRoomState {
 constructor(bank){this.bank=bank;this.bytes=new Uint8Array(0x3d18);this.v=new DataView(this.bytes.buffer);this.vms=new Map();}
 bind(offset,id,{script=true}={}){
  const vm=rebindAnm(script?this.bank:emptyBank,id,this.bytes.subarray(offset,offset+288),{resolveSprite:id=>this.bank.sprites.get(id)});this.vms.set(offset,vm);return vm;
 }
 vm(offset){if(!this.vms.has(offset))throw Error('TH06nc music room: VM not initialized '+offset.toString(16));return this.vms.get(offset);}
 sprite(offset,id){const vm=this.bind(offset,this.v.getUint16(offset+0x38,true),{script:false});vm.bindSprite(id);vm.v.setInt32(0xb4,-1,true);vm.v.setUint32(0xc4,3,true);return vm;}
}
