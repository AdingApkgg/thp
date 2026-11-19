import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {readMusicRoomTable} from '../shared/th06nc/music-room-table.mjs';
import {musicRoomFields,advanceMusicRoom} from '../shared/th06nc/music-room-update.mjs';
import {NativeFade} from '../shared/th06nc/fade.mjs';
const table=readMusicRoomTable(readFileSync('runtimes/th06nc/artifacts/scripts/th06MD.dat/musiccmt.txt')),recordSets=[table],cases=[],sha=b=>createHash('sha256').update(b).digest('hex');
const files=['arbitrary.ogg','data/bgm/th06_0.opus','data/bgm/th06_33.opus','data/bgm/th06_4294967297.opus','data/bgm/th06_-4294967295.opus','data/bgm/th06_99999999999999999999.opus'];
const alternate=new Uint8Array(0x1080);table.records.forEach((row,i)=>{for(const [offset,text]of [[0,row.titleKey],[0x22,row.descriptionKey],[0x44,files[i%files.length]]])alternate.set(new TextEncoder().encode(text),i*0x84+offset);});recordSets.push(readMusicRoomTable(new Uint8Array(),{destination:alternate}));recordSets[1].records=table.records.map((r,i)=>({...r,file:files[i%files.length]}));
function add(set,before,held,previous){
 const index=cases.length,fill=index%2?165:0,bytes=new Uint8Array(0x3d18).fill(fill),v=new DataView(bytes.buffer);for(const [key,offset]of Object.entries(musicRoomFields))v.setInt32(offset,before[key],true);v.setUint8(0x2424,Number(before.leaving));v.setUint8(0x2425,Number(before.playMark));v.setBigUint64(0x2438,0x1000n,true);
 const fade=index%7===0?null:new NativeFade();if(fade){fade.state.set(Uint8Array.from({length:56},(_,i)=>(i*3+index)&255));fade.v.setInt32(0x34,index%4,true);fade.v.setInt32(0x28,[0,127,255][index%3],true);}const beforeFade=fade?[...fade.state]:null,environment={gameState:9},calls=[],result=advanceMusicRoom({bytes,v},{held,previous,records:recordSets[set].records,unlockedMask:before.unlockedMask,fade,environment,advanceAnimation:offset=>calls.push({kind:'animation',offset}),publishDescription:(key,initial)=>calls.push({kind:'description',key,initial}),playMusic:file=>calls.push({kind:'music',file})});
 cases.push({set,before,held,previous,fill,beforeFade,afterFade:fade?[...fade.state]:null,gameState:environment.gameState,calls,result,ownerSha256:sha(bytes)});
}
for(let set=0;set<2;set++)for(const state of [0,1,2])for(const selection of [0,8,9,17])for(const clock of [0,8])for(const held of [0,16,32,48,256,272,288,304,512,768])for(const previous of [0,held])for(const unlockedMask of [0,1,0x3ffff]){
 const i=cases.length;add(set,{selection,playingIndex:0,count:18,exitClock:0,pulse:[-1,0,71,2147483647][i%4],warnedIndex:i%3?selection:-1,clock,entryTicks:[0,44,45,2147483647][i%4],scroll:Math.max(0,selection-9),state,leaving:false,playMark:Boolean(i%2),unlockedMask},held,previous);
}
for(const exitClock of [0,28,29,30,-1,2147483647])for(const state of [0,1,2])for(const held of [0,256,512])add(0,{selection:0,playingIndex:0,count:18,exitClock,pulse:71,warnedIndex:-1,clock:8,entryTicks:44,scroll:0,state,leaving:true,playMark:false,unlockedMask:0},held,0);
console.log(JSON.stringify({recordSets:recordSets.map(r=>({records:r.records,bytes:Buffer.from(r.bytes).toString('hex')})),cases}));
