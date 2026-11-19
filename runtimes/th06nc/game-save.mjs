import {GameAchievements} from './game-achievements.mjs';
import {readConfigName,writeConfigName} from '../../shared/th06nc/config-name.mjs';
import {createGameConfig,defaultEnvironmentConfig,acceptGameConfig,validGameConfig,validEnvironmentConfig} from '../../shared/th06nc/config-file.mjs';
import {decodeReplayFile} from '../../shared/th06nc/replay-file.mjs';
import {ScoreSave} from '../../shared/th06nc/score-save.mjs';
import {ScoreStats} from '../../shared/th06nc/score-stats.mjs';
import {encodeCanonicalScore} from '../../shared/th06nc/score-canonical.mjs';
import {NativeRng} from '../../shared/th06nc/rng.mjs';
import {markMusicUnlocked} from '../../shared/th06nc/music-unlock.mjs';
const pathPattern=/^replay\/th6_(0[1-9]|[1-5][0-9]|60)\.rpy$/;
export class GameSave {
 constructor({databaseName='th06nc-save-v1'}={}){this.configBytes=createGameConfig();this.runtimeKeys=this.configBytes.slice(0,10);this.environmentConfig=defaultEnvironmentConfig();this.configCommits={game:0,environment:0};this.configurationError=null;this.configurationQueue=Promise.resolve();this.databaseName=databaseName;this.db=null;this.replays=new Map();this.invalid=[];this.lastName='';this.lastWritten=null;this.score=new ScoreSave();this.stats=new ScoreStats();this.saveRng=new NativeRng();this.scoreBytes=null;this.scoreInvalidBytes=null;this.lastSaveError=null;}
 async open(){
  this.db=await new Promise((resolve,reject)=>{const request=indexedDB.open(this.databaseName,1);request.onupgradeneeded=()=>{const db=request.result;db.createObjectStore('replays',{keyPath:'path'});db.createObjectStore('config');};request.onsuccess=()=>resolve(request.result);request.onerror=()=>reject(request.error);});
  const transaction=this.db.transaction(['replays','config'],'readonly'),files=transaction.objectStore('replays').getAll(),config=transaction.objectStore('config'),name=config.get('lastName'),score=config.get('scoreFile'),gameConfig=config.get('gameConfig'),environmentConfig=config.get('environmentConfig');await new Promise((resolve,reject)=>{transaction.oncomplete=resolve;transaction.onabort=()=>reject(transaction.error);transaction.onerror=()=>reject(transaction.error);});this.lastName=typeof name.result==='string'?name.result:'';let acceptedConfig=false;
  if(gameConfig.result!=null){const accepted=acceptGameConfig(new Uint8Array(gameConfig.result));if(accepted){this.configBytes.set(accepted.bytes);this.runtimeKeys.set(accepted.keys);acceptedConfig=true;}else this.invalid.push({path:'th06.cfg',error:'Invalid configuration'});}
  if(!acceptedConfig&&this.lastName)writeConfigName(this.configBytes,Uint8Array.from(this.lastName,c=>c.charCodeAt(0)&255));this.lastName=String.fromCharCode(...readConfigName(this.configBytes).subarray(0,8));
  if(environmentConfig.result!=null){const bytes=new Uint8Array(environmentConfig.result);if(validEnvironmentConfig(bytes))this.environmentConfig.set(bytes);else this.invalid.push({path:'th06.env',error:'Invalid display configuration'});}
  if(score.result!=null){const bytes=new Uint8Array(score.result);try{this.score=new ScoreSave(bytes);this.scoreBytes=bytes;}catch(reason){this.scoreInvalidBytes=bytes;this.invalid.push({path:'score.dat',error:String(reason.message)});}}
  for(const file of files.result){try{if(!pathPattern.test(file.path))throw Error('Invalid replay slot');const bytes=new Uint8Array(file.data),decoded=decodeReplayFile(bytes);this.replays.set(file.path,{bytes,decoded});}catch(reason){this.invalid.push({path:file.path,error:String(reason.message)});}}
  this.stats.loadBoot(this.score.file.records);
  this.achievements=new GameAchievements(this.db);await this.achievements.open();
 }
 enterTitle(){this.stats.loadTitle(this.score.file.records);}
 enterResult(state,environment){this.stats.loadResult(this.score.file.records,{...environment,state,stage:environment.stageIndex});}
 markMusic(path,{ownerState=0,replayPlayback=false}={}){markMusicUnlocked(this.stats.music,{path,ownerState,blocked:replayPlayback});}
 readReplayHeader(path){return this.replays.get(path)?.decoded.header.slice()??null;}
 replayFile(path){return this.replays.get(path)?.bytes.slice()??null;}
 scoreFile(){return this.scoreBytes?.slice()??null;}
 configurationOperation(operation){
  const pending=this.configurationQueue.then(operation);
  this.configurationQueue=pending.catch(()=>{});
  return pending;
 }
 writeConfiguration(kind){
  return this.configurationOperation(async()=>{
   const game=kind==='game';
   if(!game&&kind!=='environment')throw Error('TH06nc config: unknown record');
   const bytes=(game?this.configBytes:this.environmentConfig).slice();
   if(!(game?validGameConfig(bytes):validEnvironmentConfig(bytes)))throw Error('TH06nc config: invalid record');
   const transaction=this.db.transaction('config','readwrite');
   transaction.objectStore('config').put(bytes.buffer,game?'gameConfig':'environmentConfig');
   try{
    await this.complete(transaction);
    this.configCommits[kind]++;
    this.configurationError=null;
   }catch(reason){
    this.configurationError=String(reason?.message??reason);
    throw reason;
   }
  });
 }
 writeName(name){
  return this.configurationOperation(async()=>{
   const config=this.configBytes.slice();
   writeConfigName(config,Uint8Array.from(name,c=>c.charCodeAt(0)&255));
   const transaction=this.db.transaction('config','readwrite');
   const store=transaction.objectStore('config');
   store.put(name,'lastName');
   store.put(config.buffer,'gameConfig');
   try{
    await this.complete(transaction);
    // Preserve options edited while this transaction was committing.
    this.configBytes.set(config.subarray(32,41),32);
    this.lastName=String.fromCharCode(...readConfigName(config).subarray(0,8));
    this.lastSaveError=null;
   }catch(reason){
    this.lastSaveError=String(reason?.message??reason);
    throw reason;
   }
  });
 }
 complete(transaction){return new Promise((resolve,reject)=>{transaction.oncomplete=resolve;transaction.onabort=()=>reject(transaction.error??Error('TH06nc save: transaction aborted'));transaction.onerror=()=>reject(transaction.error??Error('TH06nc save: transaction failed'));});}
 async writeScores(name=this.lastName,rng=this.saveRng){
  if(!this.db)throw Error('TH06nc save: database not open');const bytes=encodeCanonicalScore({rng,tables:this.score.tables,stats:this.stats}),restored=new ScoreSave(bytes),transaction=this.db.transaction('config','readwrite'),store=transaction.objectStore('config');store.put(bytes.buffer,'scoreFile');store.put(name,'lastName');if(this.scoreInvalidBytes)store.put(this.scoreInvalidBytes.buffer.slice(0),'scoreFileInvalidBackup');
  try{await this.complete(transaction);this.scoreBytes=bytes;this.score=restored;this.lastName=name;this.scoreInvalidBytes=null;this.invalid=this.invalid.filter(x=>x.path!=='score.dat');this.lastSaveError=null;return {bytes:bytes.length,records:restored.records().length};}catch(reason){this.lastSaveError=String(reason?.message??reason);throw reason;}
 }
 async writeReplay(path,input){
  if(!this.db)throw Error('TH06nc save: database not open');if(!pathPattern.test(path))throw Error('TH06nc save: invalid replay slot');const bytes=input.slice(),decoded=decodeReplayFile(bytes),name=String.fromCharCode(...decoded.header.subarray(29,37)),transaction=this.db.transaction(['replays','config'],'readwrite');transaction.objectStore('replays').put({path,data:bytes.buffer});transaction.objectStore('config').put(name,'lastName');
  try{await this.complete(transaction);this.replays.set(path,{bytes,decoded});this.lastName=name;this.lastWritten=path;this.lastSaveError=null;return {path,bytes:bytes.length};}catch(reason){this.lastSaveError=String(reason?.message??reason);throw reason;}
 }
 report(){const string=(bytes,p)=>String.fromCharCode(...bytes.subarray(p,p+8)).replace(/\0.*$/,'');return {achievements:this.achievements?.report()??null,configuration:{game:[...this.configBytes],keys:[...this.runtimeKeys],environment:[...this.environmentConfig],commits:{...this.configCommits},error:this.configurationError},backend:'indexedDB',open:Boolean(this.db),musicUnlockedMask:new DataView(this.stats.music.buffer,this.stats.music.byteOffset,16).getUint32(12,true),lastName:this.lastName,lastWritten:this.lastWritten,scoreBytes:this.scoreBytes?.length??0,committedScores:this.scoreBytes?new ScoreSave(this.scoreBytes).records():[],lastSaveError:this.lastSaveError,invalid:[...this.invalid],replays:[...this.replays].map(([path,{bytes,decoded}])=>({path,bytes:bytes.length,mode:decoded.header[6],profile:decoded.header[7],difficulty:decoded.header[8],name:string(decoded.header,29),date:string(decoded.header,20),stages:decoded.stageOffsets.map((offset,i)=>offset===null?null:i+1).filter(x=>x!==null)}))};}
}
