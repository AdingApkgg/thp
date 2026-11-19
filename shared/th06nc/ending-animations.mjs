import {rebindAnm} from './anm-rebind.mjs';
// Views over the ending owner's sixteen ANM slots. Cached text programs are
// resolved by the supplied bank; cache production remains an external owner.
export class EndingAnimations {
 constructor(bank,bytes=new Uint8Array(0x1280)){if(!(bytes instanceof Uint8Array)||bytes.length!==0x1280)throw Error('TH06nc ending ANM: invalid owner');this.bank=bank;this.bytes=bytes;this.anms=new Map();}
 slot(offset){if(!Number.isInteger(offset)||offset<0x38||offset>0x1118||(offset-0x38)%288!==0)throw Error('TH06nc ending ANM: invalid slot');return this.bytes.subarray(offset,offset+288);}
 bind(offset,id){const raw=this.slot(offset),v=new DataView(raw.buffer,raw.byteOffset,raw.byteLength);for(const p of [0x18,0x1c,0x20,0xc8,0xcc,0xd0])v.setUint32(p,0,true);v.setUint16(0x108,0xf0f,true);return this.prepareText(offset,id);}
 prepareText(offset,id){const vm=rebindAnm(this.bank,id,this.slot(offset));this.anms.set(offset,vm);return vm;}
 bindSprite(offset,id){const vm=this.anms.get(offset);if(!vm)throw Error('TH06nc ending ANM: missing bound script');vm.bindSprite(id);}
 tick(offset){const vm=this.anms.get(offset);if(!vm)throw Error('TH06nc ending ANM: missing updater');return vm.tick();}
 vm(offset){const vm=this.anms.get(offset);if(!vm)throw Error('TH06nc ending ANM: missing VM');return vm;}
}
