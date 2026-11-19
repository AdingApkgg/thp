import {rebindAnm} from './anm-rebind.mjs';
const F=Math.fround;
export function playerAssetPlan(character){if(character!==0&&character!==1)throw Error('TH06nc: invalid player character');return {file:`player0${character}.anm`,archive:'th06CM.dat',slot:5,base:0x420};}
const shooting=[0x14006a840n,0x14006a860n,0x14006a880n,0x14006a8a0n],bombs=[[0x14000d1a0n,0x14000d9c0n],[0x14000db50n,0x14000e130n],[0x14000e270n,0x14000e650n],[0x14000e7f0n,0x14000ebe0n]];
// Actual character initializer 68160..687e2, preserving untouched owner fields.
export function initializePlayer(state,{anmBank,environment={},character=environment.character??0,shot=environment.shot??0,skipIntro=Boolean(environment.spellPractice)}={}){
 playerAssetPlan(character);if(shot!==0&&shot!==1)throw Error('TH06nc: invalid player shot type');
 const v=new DataView(state.buffer,state.byteOffset,state.byteLength),anms=new Map(),profile=character*2+shot,speed=character===0?4:5,focusSpeed=F(speed*F(0.5)),sf=(p,x)=>v.setFloat32(p,F(x),true),si=(p,x)=>v.setInt32(p,x,true);
 const bind=(offset,id)=>{const vm=rebindAnm(anmBank,id,state.subarray(offset,offset+288),{randomU16:environment.rng?()=>environment.rng.next16():null});anms.set(offset,vm);return vm;};
 bind(0x78c8,0x420);
 for(const p of [0x7888,0x7894,0x7738])sf(p,0.49);sf(0x7730,192);sf(0x7734,384);
 for(let i=0;i<32;i++)si(0x180+i*12,0);
 v.setBigUint64(0x774c,0x3fa00000n,true);sf(0x9f28,12);sf(0x9f2c,12);sf(0x9f30,5);
 sf(0x7860,speed);sf(0x7864,focusSpeed);const root=F(Math.sqrt(F(2)));sf(0x7868,F(F(speed)/root));sf(0x786c,F(focusSpeed/root));
 for(const p of [0x7870,0x7878,0x7720,0x7728])v.setBigUint64(p,shooting[profile],true);
 v.setUint8(0x7898,skipIntro?0:1);si(0x7858,skipIntro?0:120);si(0x7854,-999);v.setUint8(0x79f8,0);
 bind(0x9f38,0x4a0);bind(0xa058,0x4a1);
 for(let i=0;i<80;i++)v.setUint16(0x420+i*0x170,0,true);v.setBigUint64(0x408,0xfffffffffffffc19n,true);
 v.setBigUint64(0x9ed0,bombs[profile][0],true);v.setBigUint64(0x9ed8,bombs[profile][1],true);v.setUint8(0x9ec8,0);
 for(const p of [0x79ec,0x79f4])si(p,0);for(const p of [0x79e8,0x79f0])si(p,-999);sf(0x7714,1);sf(0x7710,1);si(0x773c,8);
 return anms;
}
