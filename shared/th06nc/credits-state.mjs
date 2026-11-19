import {AnmBank} from './anm-bank.mjs';
import {rebindAnm} from './anm-rebind.mjs';
const emptyBank=new AnmBank();
export const creditsTextAsset={archive:'th06IN.dat',file:'text.anm',slot:0,base:0x72f};
export class CreditsState {
 constructor(bank){this.bank=bank;this.bytes=new Uint8Array(0x31c8);this.v=new DataView(this.bytes.buffer);this.vms=new Map();}
 vm(offset){if(!this.vms.has(offset))throw Error('TH06nc credits: missing text VM');return this.vms.get(offset);}
 sprite(offset,id){const vm=rebindAnm(emptyBank,this.v.getUint16(offset+0x38,true),this.bytes.subarray(offset,offset+288),{resolveSprite:id=>this.bank.sprites.get(id)});vm.bindSprite(id);vm.v.setInt32(0xb4,-1,true);vm.v.setUint32(0xc4,3,true);this.vms.set(offset,vm);return vm;}
}
