import{StoppedSoundBuffer}from'./StoppedSoundBuffer.mjs';import{SoundBufferPlaybackV2}from'./SoundBufferPlaybackV2.mjs';
//Private V37 platform bridge. A CPU driver event is consumed once; live browser
//cursor/status is fed back before the next game update. This remains a playback
//prototype, with native device timing/mixing and BGM integration still pending.
export class SoundBankOrderedWebPlaybackV2 {
  constructor(context,runtime){this.context=context;this.runtime=runtime;this.buffers=new Map;this.sharedAudio=new Map;this.driverCalls=0;this.statusSyncs=0;}
  bytes(p,n){return new Uint8Array(this.runtime.memory.buffer,p,n);}
  initialize(){
    const c=this.runtime;if(c.campaign_audio_prepared()!==1||c.campaign_audio_buffer_count()!==88)throw Error('Sound bank is not initialized');
    for(let i=0;i<88;++i){
      const token=c.campaign_audio_buffer_info(i,0)>>>0,sample=c.campaign_audio_buffer_info(i,1)>>>0,n=c.campaign_audio_buffer_info(i,2)>>>0;
      const format=new Uint8Array(this.bytes(c.campaign_audio_buffer_format(i),18)),pcm=new Uint8Array(this.bytes(c.campaign_audio_buffer_data(i),n)),storage=new StoppedSoundBuffer(format,pcm);
      const volume=c.campaign_audio_buffer_info(i,6)|0,pan=c.campaign_audio_buffer_info(i,5)|0,position=c.campaign_audio_buffer_info(i,4)>>>0;
      if(storage.setVolume(volume)||storage.setPan(pan)||storage.setPosition(position))throw Error('Unsupported initial sound properties');
      const audioBuffer=this.sharedAudio.get(sample),playback=new SoundBufferPlaybackV2(this.context,storage,{audioBuffer,destination:this.orderedMixer.slot(i)});if(!audioBuffer)this.sharedAudio.set(sample,playback.audioBuffer);this.buffers.set(token,{index:i,playback});
    }
    //User-enabled playback starts from this live point. Bootstrap audio events
    //were generated while the private session advanced without an audio clock.
    c.campaign_audio_clear_events();this.syncStatus();
  }
  currentFrame(){return Math.round(this.context.currentTime*this.context.sampleRate);}
  syncStatus(frame=this.currentFrame()){
    for(const[token,{playback}]of this.buffers){const s=playback.status(frame);if(this.runtime.campaign_audio_buffer_state(token,s.status,s.play)!==1)throw Error('Sound state bridge rejected a buffer');}
    ++this.statusSyncs;
  }
  consume(frame=this.currentFrame()){
    const c=this.runtime,n=c.campaign_audio_events_bytes(),raw=new Uint8Array(this.bytes(c.campaign_audio_events_data(),n)),v=new DataView(raw.buffer);let at=0;
    while(at<n){
      if(n-at<12)throw Error('Truncated sound event header');const op=v.getUint32(at,true),count=v.getUint32(at+4,true),payload=v.getUint32(at+8,true);at+=12;
      if(count>64||at+count*4+payload>n)throw Error('Truncated sound event payload');const args=Array.from({length:count},(_,i)=>v.getUint32(at+i*4,true));at+=count*4+payload;
      if(![0x48,0x34,0x40,0x3c,0x30].includes(op))continue;const buffer=this.buffers.get(args[0]);if(!buffer)throw Error('Unknown sound buffer token');const expected=args.at(-1)>>>0;
      if(expected<0x80000000){const hr=buffer.playback.call(op,args.slice(1,-1),frame);if(hr!==expected)throw Error('Browser sound driver HRESULT differs from CPU event');}
      ++this.driverCalls;
    }
    c.campaign_audio_clear_events();
  }
  stop(){const frame=this.currentFrame();for(const{playback}of this.buffers.values())playback.stop(frame);this.syncStatus(frame);}
  dispose(){const frame=this.currentFrame();for(const{playback}of this.buffers.values())playback.dispose(frame);this.buffers.clear();this.sharedAudio.clear();}
}
