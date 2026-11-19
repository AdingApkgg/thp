import {readFileSync} from 'node:fs';
import {AnmBank} from '../shared/th06nc/anm-bank.mjs';
import {readAnm} from '../shared/th06nc/anm.mjs';
import {readMessagePack} from '../shared/th06nc/messagepack.mjs';
import {MusicRoomState} from '../shared/th06nc/music-room-state.mjs';
import {publishMusicRoomDescription} from '../shared/th06nc/music-room-description.mjs';
const ref={archive:'th06IN.dat',file:'text.anm',slot:0,base:0x72f},resource=readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+ref.archive+'/'+ref.file)),localized=readMessagePack(readFileSync('runtimes/th06nc/artifacts/scripts/th06IN.dat/localization.msgpack')),cases=[];
for(const language of ['zh-CN','ja','en'])for(const initial of [false,true])for(const key of ['MD_00_DESC','MD_17_DESC','MD_LOCKED_DESC','EMPTY','NEWLINES','LONG','CRLF']){
 const bank=new AnmBank();bank.load(resource,ref.base,{slot:ref.slot});const owner=new MusicRoomState(bank),localization={...Object.fromEntries(Object.entries(localized).map(([k,v])=>[k,v[language]??k])),EMPTY:'',NEWLINES:'\n\n\n',LONG:Array.from({length:19},(_,i)=>'Line '+i+' 曲目').join('\n'),CRLF:'One\r\n\r\nTwo\r\n'},publish=(vm,r)=>{[1,1,120,36].forEach((x,i)=>vm.v.setInt32(0x10c+i*4,x,true));vm.v.setUint32(0xc4,vm.v.getUint32(0xc4,true)|1,true);};
 if(!initial)publishMusicRoomDescription(owner,'LONG',{initial:true,localization,publishText:publish});const before=Buffer.from(owner.bytes).toString('hex'),calls=[];publishMusicRoomDescription(owner,key,{initial,localization,publishText:(vm,r)=>{calls.push(r);publish(vm,r);}});const lines=localization[key].split('\n');if(lines.at(-1)==='')lines.pop();cases.push({language,key,initial,lines,before,after:Buffer.from(owner.bytes).toString('hex'),calls});
}
console.log(JSON.stringify({ref,cases}));
