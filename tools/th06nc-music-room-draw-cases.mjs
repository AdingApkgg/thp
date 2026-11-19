import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {readAnm} from '../shared/th06nc/anm.mjs';
import {readMessagePack} from '../shared/th06nc/messagepack.mjs';
import {AnmBank} from '../shared/th06nc/anm-bank.mjs';
import {asciiFontAssets} from '../shared/th06nc/ascii-layout.mjs';
import {musicRoomAssets} from '../shared/th06nc/music-room-state.mjs';
import {readMusicRoomTable} from '../shared/th06nc/music-room-table.mjs';
import {MusicRoomScene} from '../shared/th06nc/music-room-scene.mjs';
const refs=[...musicRoomAssets,{archive:'th06IN.dat',file:'text.anm',slot:0,base:0x72f},...asciiFontAssets],bank=new AnmBank();for(const ref of refs)bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+ref.archive+'/'+ref.file)),ref.base,{slot:ref.slot});
const records=readMusicRoomTable(readFileSync('runtimes/th06nc/artifacts/scripts/th06MD.dat/musiccmt.txt')).records,localized=readMessagePack(readFileSync('runtimes/th06nc/artifacts/scripts/th06IN.dat/localization.msgpack')),localization=Object.fromEntries(Object.entries(localized).map(([k,v])=>[k,v['zh-CN']??k])),scene=new MusicRoomScene(bank,{records,unlockedMask:0x3ffff,localization,playMusic:()=>{},publishText:(vm,r)=>{[1,1,120,36].forEach((x,i)=>vm.v.setInt32(0x10c+i*4,x,true));vm.v.setUint32(0xc4,vm.v.getUint32(0xc4,true)|1,true);}}),baseline=scene.state.bytes.slice(),asciiBaseline=scene.ascii.bytes.slice(),cases=[],sha=b=>createHash('sha256').update(b).digest('hex');
for(const selection of [0,9,17])for(const ticks of [0,1,3,12,18,30,45])for(const pulse of [0,15,30,42,60,71])for(const playing of [false,true])for(const cursor of [0,250,256]){
 scene.state.bytes.set(baseline);scene.ascii.bytes.set(asciiBaseline);const v=scene.state.v,scroll=selection===17?8:0;v.setInt32(0,selection,true);v.setInt32(0x2b08,scroll,true);v.setInt32(0x2444,ticks,true);v.setInt32(0x242c,pulse,true);v.setUint8(0x2425,Number(playing));v.setInt32(0x2408,selection,true);scene.ascii.v.setInt32(0x7bb0,cursor,true);const calls=[];scene.draw((vm,r)=>calls.push({...r,state:Buffer.from(vm.state).toString('hex')}));cases.push({selection,scroll,ticks,pulse,playing,cursor,calls,ownerSha256:sha(scene.state.bytes),asciiSha256:sha(scene.ascii.bytes)});
}
console.log(JSON.stringify({refs,baseline:Buffer.from(baseline).toString('hex'),cases}));
