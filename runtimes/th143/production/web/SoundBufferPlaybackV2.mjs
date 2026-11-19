import{SoundHresult}from'./StoppedSoundBuffer.mjs';
import{createSoundAudioBuffer}from'./SoundPcmAudioBuffer.mjs';

//Unaccepted physical playback prototype. PCM conversion is independently
//verified; gain/pan output, resampling, live latency and DirectSound clock/status
//equivalence still need original-device evidence. Commands use context sample
//frames so offline tests do not introduce a second wall-clock approximation.
export class SoundBufferPlaybackV2 {
  #context;#storage;#audio;#left;#right;#split;#merge;#source=null;
  #position=0;#start=0;#startPosition=0;#playing=false;#loop=false;#lastFrame=0;
  constructor(context,storage,{audioBuffer=null,destination=context.destination}={}){
    this.#context=context;this.#storage=storage;this.#audio=audioBuffer||createSoundAudioBuffer(context,storage);
    this.#left=context.createGain();this.#right=context.createGain();this.#merge=context.createChannelMerger(2);
    this.#left.connect(this.#merge,0,0);this.#right.connect(this.#merge,0,1);this.#merge.connect(destination);
    this.#position=storage.position/storage.blockAlign;
    this.#gains(0);
  }
  get audioBuffer(){return this.#audio;}
  get storage(){return this.#storage;}
  get sampleRate(){return this.#storage.sampleRate;}
  get contextSampleRate(){return this.#context.sampleRate;}
  currentFrame(){return Math.round(this.#context.currentTime*this.#context.sampleRate);}
  #frame(frame){if(!Number.isInteger(frame)||frame<0||frame>0xffffffff||frame<this.#lastFrame)throw new RangeError('Audio command frame must be a monotonic uint32');this.#lastFrame=frame;return frame;}
  #gains(frame){const time=frame/this.#context.sampleRate,volume=this.#storage.volume,pan=this.#storage.pan;this.#left.gain.setValueAtTime(10**((volume-Math.max(pan,0))/2000),time);this.#right.gain.setValueAtTime(10**((volume+Math.min(pan,0))/2000),time);}
  #advance(frame){
    if(!this.#playing)return;
    const at=this.#startPosition+(frame-this.#start)*this.#storage.sampleRate/this.#context.sampleRate,total=this.#audio.length;
    if(!this.#loop&&at>=total){this.#playing=false;this.#position=0;this.#source=null;}
    else this.#position=Math.floor(at)%total;
  }
  #begin(frame,phase=this.#position){
    const source=this.#context.createBufferSource();source.buffer=this.#audio;source.loop=this.#loop;
    if(this.#storage.channels===1){source.connect(this.#left);source.connect(this.#right);}
    else{const split=this.#context.createChannelSplitter(2);source.connect(split);split.connect(this.#left,0);split.connect(this.#right,1);source.onended=()=>{source.disconnect();split.disconnect();};}
    if(!source.onended)source.onended=()=>source.disconnect();
    source.start(frame/this.#context.sampleRate,phase/this.#storage.sampleRate);this.#source=source;this.#start=frame;this.#startPosition=phase;this.#position=Math.floor(phase);this.#playing=true;
  }
  status(frame=this.currentFrame()){frame=this.#frame(frame);this.#advance(frame);return{hr:0,status:this.#playing?(1|(this.#loop?4:0)):0,play:this.#position*this.#storage.blockAlign};}
  setVolume(value,frame=this.currentFrame()){frame=this.#frame(frame);const hr=this.#storage.setVolume(value);if(hr===0)this.#gains(frame);return hr;}
  setPan(value,frame=this.currentFrame()){frame=this.#frame(frame);const hr=this.#storage.setPan(value);if(hr===0)this.#gains(frame);return hr;}
  setPosition(value,frame=this.currentFrame()){
    frame=this.#frame(frame);this.#advance(frame);const hr=this.#storage.setPosition(value);if(hr)return hr;
    const playing=this.#playing;if(playing)this.#source.stop(frame/this.#context.sampleRate);this.#source=null;this.#playing=false;this.#position=this.#storage.position/this.#storage.blockAlign;if(playing)this.#begin(frame);return 0;
  }
  play(reserved=0,priority=0,flags=0,frame=this.currentFrame()){
    frame=this.#frame(frame);this.#advance(frame);if(reserved!==0||priority!==0||(flags&~1)!==0)return SoundHresult.invalid;
    const loop=!!(flags&1);
    if(this.#playing){if(loop!==this.#loop){const phase=(this.#startPosition+(frame-this.#start)*this.#storage.sampleRate/this.#context.sampleRate)%this.#audio.length;this.#source.stop(frame/this.#context.sampleRate);this.#loop=loop;this.#begin(frame,phase);}return 0;}
    this.#loop=loop;this.#begin(frame);return 0;
  }
  stop(frame=this.currentFrame()){
    frame=this.#frame(frame);this.#advance(frame);if(this.#playing)this.#source.stop(frame/this.#context.sampleRate);this.#playing=false;this.#source=null;return 0;
  }
  call(method,args,frame=this.currentFrame()){
    if(method===0x48&&args.length===0)return this.stop(frame);
    if(method===0x34&&args.length===1)return this.setPosition(args[0],frame);
    if(method===0x3c&&args.length===1)return this.setVolume(args[0]|0,frame);
    if(method===0x40&&args.length===1)return this.setPan(args[0]|0,frame);
    if(method===0x30&&args.length===3)return this.play(args[0],args[1],args[2],frame);
    throw new RangeError('Unsupported sound buffer operation');
  }
  dispose(frame=this.currentFrame()){this.stop(frame);this.#left.disconnect();this.#right.disconnect();this.#merge.disconnect();}
}
