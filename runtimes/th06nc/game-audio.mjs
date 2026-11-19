import {soundFiles,soundDefinitions,consumeSoundQueue} from '../../shared/th06nc/sound-queue.mjs';
// Web Audio transport. The request queue and source table have native evidence;
// platform mixer/resampler equivalence remains outside that evidence.
export class GameAudio {
 constructor(context=new AudioContext()){
  this.context=context;this.buffers=new Map();this.voices=new Map();this.volumes=new Map();this.volume=10;this.started=0;this.restarted=0;this.lastSound=null;this.musicBuffers=new Map();this.musicRequests=new Map();this.musicManifestRequest=null;this.music=null;this.musicSerial=0;
 }
 async prepare(load){await Promise.all(soundFiles.map(async file=>{const raw=await load('./artifacts/audio/'+file);const buffer=await this.context.decodeAudioData(raw.slice().buffer);if(buffer.numberOfChannels<1||buffer.length<1)throw Error('TH06nc audio: empty '+file);this.buffers.set(file,buffer);}));}
 unlock(){return this.context.resume();}
 async prepareMusicManifest(load){
  if(this.musicManifest)return this.musicManifest;
  if(!this.musicManifestRequest){
   const request=(async()=>JSON.parse(new TextDecoder().decode(await load('./artifacts/audio/music-manifest.json'))))();
   this.musicManifestRequest=request;
   try{this.musicManifest=await request;}
   finally{if(this.musicManifestRequest===request)this.musicManifestRequest=null;}
  }else await this.musicManifestRequest;
  return this.musicManifest;
 }
 async prepareMusicTrack(file,load){
  if(this.musicBuffers.has(file))return this.musicBuffers.get(file);
  if(this.musicRequests.has(file))return this.musicRequests.get(file);
  const request=(async()=>{
   const [,directory,stem]=file.match(/^data\/(bgm2?)\/(th06_\d{2})\.opus$/),metadata=this.musicManifest.find(track=>track.directory===directory&&track.originalFile===stem+'.opus');if(!metadata)throw Error('TH06nc audio: music metadata missing '+file);
   const raw=await load('./artifacts/audio/'+directory+'/'+stem+'.ogg'),buffer=await this.context.decodeAudioData(raw.slice().buffer);if(Math.abs(buffer.duration-metadata.samples/48000)>1/this.context.sampleRate)throw Error('TH06nc audio: music duration mismatch '+file);
   const prepared={buffer,metadata};this.musicBuffers.set(file,prepared);return prepared;
  })();
  this.musicRequests.set(file,request);
  try{return await request;}finally{if(this.musicRequests.get(file)===request)this.musicRequests.delete(file);}
 }
 async prepareMusic(files,load){
  await this.prepareMusicManifest(load);
  const keys=new Set(files.filter(file=>/^data\/bgm2?\/th06_\d{2}\.opus$/.test(file)));
  for(const file of keys)await this.prepareMusicTrack(file,load);
  for(const file of this.musicBuffers.keys())if(!keys.has(file)&&file!==this.music?.file&&!/^data\/bgm2?\/th06_01\.opus$/.test(file))this.musicBuffers.delete(file);
 }
 playMusic(file,state){
  if(this.music?.file===file)return state.handle;
  const prepared=this.musicBuffers.get(file);if(!prepared)throw Error('TH06nc audio: music not prepared '+file);
  this.stopMusic();const source=this.context.createBufferSource(),gain=this.context.createGain();source.buffer=prepared.buffer;source.loop=true;source.loopStart=prepared.metadata.loopStart/48000;source.loopEnd=Math.min(prepared.metadata.loopEnd/48000,prepared.buffer.duration);source.connect(gain);gain.connect(this.context.destination);source.start();const handle=++this.musicSerial;this.music={file,source,gain,handle,metadata:prepared.metadata};Object.assign(state,{handle,playing:true,fading:false,pendingValue:0});return handle;
 }
 musicVolume(value){if(this.music)this.music.gain.gain.value=10**(Math.max(-10000,Math.min(0,value-10000))/2000);}
 stopMusic(){if(this.music){this.music.source.stop();this.music.source.disconnect();this.music.gain.disconnect();this.music=null;}}
 consume(slots){return consumeSoundQueue(slots,{volume:this.volume,setVolume:({handle,value})=>this.volumes.set(handle,value),playSound:({handle})=>this.play(handle)});}
 play(id){
  const definition=soundDefinitions[id],buffer=this.buffers.get(definition?.file);if(!buffer)throw Error('TH06nc audio: sound not prepared '+id);
  const old=this.voices.get(id);if(old){old.source.stop();old.source.disconnect();old.gain.disconnect();this.restarted++;}
  const source=this.context.createBufferSource(),gain=this.context.createGain(),centibels=Math.max(-10000,Math.min(0,(this.volumes.get(id)??10000)-10000));
  source.buffer=buffer;gain.gain.value=10**(centibels/2000);source.connect(gain);gain.connect(this.context.destination);
  const voice={source,gain};this.voices.set(id,voice);source.onended=()=>{if(this.voices.get(id)===voice)this.voices.delete(id);source.disconnect();gain.disconnect();};source.start();this.started++;this.lastSound=id;
 }
 stopSounds(){for(const voice of this.voices.values())voice.source.stop();this.voices.clear();}
 report(){return {state:this.context.state,decoded:this.buffers.size,started:this.started,restarted:this.restarted,voices:this.voices.size,lastSound:this.lastSound,music:this.music?{file:this.music.file,handle:this.music.handle,loopStart:this.music.source.loopStart,loopEnd:this.music.source.loopEnd,gain:this.music.gain.gain.value}:null,musicDecoded:this.musicBuffers.size,mixerEquivalent:false};}
}
