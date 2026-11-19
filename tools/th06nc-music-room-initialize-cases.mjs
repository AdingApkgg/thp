import {readFileSync} from 'node:fs';
import {readAnm} from '../shared/th06nc/anm.mjs';
import {AnmBank} from '../shared/th06nc/anm-bank.mjs';
import {readMessagePack} from '../shared/th06nc/messagepack.mjs';
import {MusicRoomState,musicRoomAssets} from '../shared/th06nc/music-room-state.mjs';
import {readMusicRoomTable} from '../shared/th06nc/music-room-table.mjs';
import {initializeMusicRoom} from '../shared/th06nc/music-room-initialize.mjs';
import {NativeFade} from '../shared/th06nc/fade.mjs';
const original=readFileSync('runtimes/th06nc/artifacts/scripts/th06MD.dat/musiccmt.txt'),table=readMusicRoomTable(original),refs=[...musicRoomAssets],resources=refs.map(ref=>readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+ref.archive+'/'+ref.file))),localized=readMessagePack(readFileSync('runtimes/th06nc/artifacts/scripts/th06IN.dat/localization.msgpack')),cases=[];
for(const language of ['zh-CN','ja','en'])for(const unlockedMask of [0,1,0x7f,0x3ffff])for(const mode of [0,2]){
 const bank=new AnmBank();refs.forEach((ref,i)=>bank.load(resources[i],ref.base,{slot:ref.slot}));const owner=new MusicRoomState(bank),fade=new NativeFade();fade.v.setInt32(0x34,mode,true);fade.v.setUint32(0x20,0x123456,true);fade.v.setInt32(0x28,127,true);const beforeFade=[...fade.state],calls=[],localization=Object.fromEntries(Object.entries(localized).map(([k,v])=>[k,v[language]??k]));
 initializeMusicRoom(owner,{records:table.records,unlockedMask,localization,fade,publishText:(vm,r)=>{calls.push({kind:'font',...r});[1,1,120,36].forEach((x,i)=>vm.v.setInt32(0x10c+i*4,x,true));vm.v.setUint32(0xc4,vm.v.getUint32(0xc4,true)|1,true);},publishDescription:(key,initial)=>calls.push({kind:'description',key,initial}),awardAchievement:key=>calls.push({kind:'achievement',key}),commitAchievements:()=>calls.push({kind:'commit'})});owner.v.setBigUint64(0x2438,0x1000n,true);cases.push({language,unlockedMask,localization:Object.fromEntries([...table.records.map(r=>r.titleKey),'MD_LOCKED_TITLE'].map(k=>[k,localization[k]])),beforeFade,afterFade:[...fade.state],calls,owner:Buffer.from(owner.bytes).toString('hex')});
}
console.log(JSON.stringify({refs,table:Buffer.from(original).toString('hex'),cases}));
