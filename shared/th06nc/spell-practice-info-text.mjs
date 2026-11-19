import {AnmBank} from './anm-bank.mjs';
import {rebindAnm} from './anm-rebind.mjs';

const emptyBank=new AnmBank();
export const spellProfileKeys=['EXE_REIMU_A_NAME','EXE_REIMU_B_NAME','EXE_MARISA_A_NAME','EXE_MARISA_B_NAME'];
export const spellBossKeys=['RUMIA','CIRNO','MEILING','PATCHOULI','SAKUYA','REMILIA','FLANDRE'].map(s=>'EXE_BOSS_NAME_'+s);
export const spellInfoTextAsset=Object.freeze({archive:'th06IN.dat',file:'text.anm',slot:0,base:0x72f});

export function createSpellInfoPublisher(group,publishText){
 if(typeof publishText!=='function')throw Error('TH06nc: spell-info publisher required');
 return (offset,sprite,text,{key=null,x=0,y=0,scale=1,color=0xffffff,header=false}={})=>{
  const old=group.slots.get(offset),bytes=old?.state??new Uint8Array(288),v=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),id=v.getUint16(0x38,true);
  const vm=rebindAnm(emptyBank,id,bytes,{resolveSprite:id=>group.bank.sprites.get(id)});vm.v.setInt32(0xb4,-1,true);vm.bindSprite(sprite);vm.v.setUint32(0xc4,vm.v.getUint32(0xc4,true)|1,true);vm.v.setUint16(0x108,0xf0f,true);group.slots.set(offset,vm);
  publishText(vm,{offset,sprite,key,text,colors:[color,0,0x10101,0x40202],size:[15,15]});
  vm.v.setUint32(0xc4,header?vm.v.getUint32(0xc4,true)&~0x700:(vm.v.getUint32(0xc4,true)&~0x300)|0x400,true);
  for(const [p,value]of [[0xc8,x],[0xcc,y],[0xd0,0],[0xe4,scale],[0xe8,scale]])vm.v.setFloat32(p,value,true);
  return vm;
 };
}

export function publishSpellInfoHeading(publish,state,profile,localization){
 const localize=key=>localization[key]??key;
 if(profile<0||profile>=4)throw Error('TH06nc: invalid spell-menu profile');
 let key='EXE_SPELL_PRACTICE_'+(state.state===28?'STAGE_SELECT':state.state===29?'SPELL_SELECT':'DIFFICULTY_SELECT');
 publish(0x16930,0x737,localize(key),{key,x:233.3333282470703,y:78.22222137451172,header:true});
 key='EXE_SPELL_PRACTICE_CHARACTER_SHOT_FMT';publish(0x19870,0x761,localize(key).replace(/%s/,()=>localize(spellProfileKeys[profile])),{key,x:233.3333282470703,y:95.11111450195312,scale:.9,header:true});
}
