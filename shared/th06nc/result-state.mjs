import {AnmBank} from './anm-bank.mjs';
import {rebindAnm} from './anm-rebind.mjs';
const emptyBank=new AnmBank();
export const resultAssets=[
 ['result.anm',68,0x7d0],['result00.anm',42,0x798],['result01.anm',43,0x7a0],['result02.anm',44,0x7a7],['result03.anm',45,0x7bd],['difficulty.anm',66,0x792],
].map(([file,slot,base])=>({archive:'th06TL.dat',file,slot,base}));
export const resultTextAsset={archive:'th06IN.dat',file:'text.anm',slot:0,base:0x72f};
// Result owner 6df00/73e93: raw ANM views and animation initialization.
// Rank lists, record loading, state dispatch and drawing are separate owners.
export class ResultState {
 constructor(anmBank,{initialize=true}={}){this.anmBank=anmBank;this.bytes=new Uint8Array(0xbb48);this.v=new DataView(this.bytes.buffer);this.anms=new Map();this.v.setInt32(0x9e7c,1,true);if(initialize)initializeResultAnimations(this);}
 vm(offset){if(!this.anms.has(offset))throw Error('TH06nc result: VM not initialized at '+offset.toString(16));return this.anms.get(offset);}
 bind(offset,id){const vm=rebindAnm(this.anmBank,id,this.bytes.subarray(offset,offset+288));this.anms.set(offset,vm);return vm;}
 resetSprite(offset,id){const old=this.v.getUint16(offset+0x38,true),vm=rebindAnm(emptyBank,old,this.bytes.subarray(offset,offset+288),{resolveSprite:id=>this.anmBank.sprites.get(id)});this.anms.set(offset,vm);vm.v.setInt32(0xb4,-1,true);vm.v.setUint32(0xc4,vm.v.getUint32(0xc4,true)|1,true);vm.bindSprite(id);return vm;}
}
export function initializeResultAnimations(state){
 const {v}=state;for(let i=0;i<5;i++)state.bind(0x3d70+i*288,0x7d0+i);
 for(let i=0;i<38;i++){const p=0xb0+i*288;for(const f of [0x18,0x1c,0x20,0xc8,0xcc,0xd0])v.setUint32(p+f,0,true);state.bind(p,0x798+i);}
 for(let i=0;i<16;i++){const p=0x2b70+i*288,vm=state.resetSprite(p,0x737+i);for(const f of [0xc8,0xcc,0xd0])v.setUint32(p+f,0,true);v.setUint32(p+0xc4,(v.getUint32(p+0xc4,true)&~0x300)|0x400,true);vm.v.setUint16(0x108,0xf0f,true);}
 state.resetSprite(0x4310,0x792);v.setBigUint64(0x43d8,0n,true);v.setUint32(0x43e0,0,true);v.setUint32(0x43d4,(v.getUint32(0x43d4,true)&~0x300)|0x400,true);
}
// Common tail 72743..727ef. State-specific input precedes these ANM ticks.
export function advanceResultCommon(state,previousState){
 const {v}=state;for(let i=0;i<38;i++)state.vm(0xb0+i*288).tick();for(let i=0;i<5;i++)state.vm(0x3d70+i*288).tick();
 const current=v.getInt32(0x9e94,true);if((previousState===0&&current===1)||(previousState===current&&(current>>>0)<=1))v.setInt32(0x4454,((v.getInt32(0x4454,true)+1)|0)%72,true);v.setInt32(0x4450,(v.getInt32(0x4450,true)+1)|0,true);
}
