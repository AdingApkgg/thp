import{OrderedAudioMixV3}from'./OrderedAudioMixV3.mjs';
import{SoundBankOrderedWebPlaybackV2}from'./SoundBankOrderedWebPlaybackV2.mjs';
import{StoppedSoundBuffer}from'./StoppedSoundBuffer.mjs';
import{SoundBufferPlaybackV2}from'./SoundBufferPlaybackV2.mjs';
import{MusicRingWebPlaybackV3}from'./MusicRingWebPlaybackV3.mjs';

//The event stream owns creation/notification data, so a recycled CPU slot can
//be created and destroyed multiple times before one browser consume call.
//Clock/cursor feedback is still a declared software platform, not native timing.
export class ReusableGameWebAudioV4 extends SoundBankOrderedWebPlaybackV2 {
  constructor(context,runtime){super(context,runtime);this.music=new Map;this.retired=new Set;this.musicNotifications=0;this.musicPatchBytes=0;this.musicCreated=0;this.musicReleased=0;this.silent=context.createGain();this.silent.gain.value=0;this.orderedMixer=null;this.initializationAbort=new AbortController();this.initialized=false;this.disposed=false;}
  assertLive(){if(this.disposed||this.initializationAbort.signal.aborted)throw new DOMException('Audio initialization closed','AbortError');}
  async initialize(){
    this.assertLive();
    this.orderedMixer=await OrderedAudioMixV3.create(this.context,104,this.initializationAbort.signal);this.assertLive();
    await this.context.audioWorklet.addModule(new URL('./MusicRingProcessorV3.mjs',import.meta.url));
    this.assertLive();super.initialize();
    const c=this.runtime;
    for(let i=0;i<c.campaign_music_buffer_count();++i)if(c.campaign_music_buffer_info(i,8)){
      const n=c.campaign_music_buffer_info(i,2),count=c.campaign_music_buffer_info(i,9);
      const record=this.createMusic(i,c.campaign_music_buffer_info(i,0)>>>0,new Uint8Array(this.bytes(c.campaign_music_buffer_format(i),18)),new Uint8Array(this.bytes(c.campaign_music_buffer_data(i),n)),0);
      this.setNotifications(record,Array.from({length:count},(_,j)=>c.campaign_music_buffer_notification(i,j)),Array.from({length:count},(_,j)=>c.campaign_music_buffer_notification_event(i,j)),0);
      for(const[op,args]of [[0x34,[c.campaign_music_buffer_info(i,4)]],[0x3c,[c.campaign_music_buffer_info(i,6)|0]],[0x40,[c.campaign_music_buffer_info(i,5)|0]]])this.musicCall(record,op,args,0);
      if(c.campaign_music_buffer_info(i,3))this.musicCall(record,0x30,[0,0,c.campaign_music_buffer_info(i,7)],0);
    }
    this.initialized=true;
  }
  createMusic(index,token,format,pcm,frame){
    if(!Number.isInteger(index)||index<0||index>=16||this.music.has(token))throw Error('Invalid or duplicate music slot');
    const v=new DataView(format.buffer,format.byteOffset,format.byteLength),rate=v.getUint32(4,true),channels=v.getUint16(2,true),bits=v.getUint16(14,true),align=v.getUint16(12,true);
    if(rate!==this.context.sampleRate||channels!==2||bits!==16||align!==4)throw Error('BGM domain requires stereo16/44100');
    const storage=new StoppedSoundBuffer(format,pcm),clock=new SoundBufferPlaybackV2(this.context,storage,{destination:this.silent});
    const node=new AudioWorkletNode(this.context,'th143-music-ring-v3',{numberOfInputs:0,numberOfOutputs:1,outputChannelCount:[2],processorOptions:{channels,bits,rate,pcm,notifications:[]}}),playback=new MusicRingWebPlaybackV3(this.context,node);
    node.connect(this.orderedMixer.slot(88+index));
    const record={index,token,n:pcm.length,align,clock,playback,notifications:[],notificationEvents:[],lastFrame:frame,last:{status:0,play:0}};
    this.music.set(token,record);++this.musicCreated;return record;
  }
  setNotifications(record,offsets,events,frame){
    if(offsets.length!==events.length||offsets.length>64)throw Error('Invalid notification table');
    record.notifications=[...offsets];record.notificationEvents=[...events];record.playback.setNotifications(offsets,frame);
  }
  musicCall(record,op,args,frame){
    const hr=record.clock.call(op,args,frame);if(hr)return hr;
    const p=record.playback;
    if(op===0x48)p.stop(frame);else if(op===0x34)p.setPosition(args[0],frame);else if(op===0x3c)p.setVolume(args[0]|0,frame);else if(op===0x40)p.setPan(args[0]|0,frame);else if(op===0x30)p.play(!!(args[2]&1),frame);
    record.last=record.clock.status(frame);record.lastFrame=frame;return hr;
  }
  syncStatus(frame=this.currentFrame()){
    super.syncStatus(frame);const c=this.runtime;c.campaign_music_clock(frame/this.context.sampleRate*1000);
    for(const record of this.music.values()){
      const state=record.clock.status(frame);
      if(c.campaign_music_buffer_state(record.token,state.status,state.play,(state.play+256*record.align)%record.n)!==1)throw Error('BGM cursor feedback rejected');
      if((record.last.status&1)&&(state.status&1)){
        const elapsed=(frame-record.lastFrame)*record.align,delta=(state.status&4)?elapsed:Math.max(0,state.play-record.last.play);
        const crossed=record.notifications.map((offset,index)=>({offset,index,distance:(offset+1-record.last.play+record.n)%record.n||record.n})).filter(n=>n.distance<=delta).sort((a,b)=>a.distance-b.distance);
        for(const notice of crossed){if(!c.campaign_music_event_live(record.notificationEvents[notice.index]))continue;if(c.campaign_music_dispatch()!==1)throw Error('BGM notification worker unavailable');++this.musicNotifications;}
      }
      record.last=state;record.lastFrame=frame;
    }
  }
  consume(frame=this.currentFrame()){
    const c=this.runtime,n=c.campaign_audio_events_bytes(),raw=new Uint8Array(this.bytes(c.campaign_audio_events_data(),n)),v=new DataView(raw.buffer);let at=0;
    while(at<n){
      if(n-at<12)throw Error('Truncated audio event');const op=v.getUint32(at,true),count=v.getUint32(at+4,true),payload=v.getUint32(at+8,true);at+=12;
      if(count>64||at+count*4+payload>n)throw Error('Invalid audio event');const args=Array.from({length:count},(_,i)=>v.getUint32(at+i*4,true));at+=count*4;const bytes=raw.subarray(at,at+payload);at+=payload;
      if(op===0x300){if(count!==3||payload!==18)throw Error('Invalid music create event');this.createMusic(args[1],args[0],bytes,new Uint8Array(args[2]),frame);continue;}
      if(op===0x301){const record=this.music.get(args[0]);if(!record)throw Error('Released unknown BGM buffer');record.clock.dispose(frame);this.retired.add(record);record.playback.retire(frame,()=>this.retired.delete(record));this.music.delete(args[0]);++this.musicReleased;continue;}
      if(op===0x302){const record=this.music.get(args[0]);if(!record||payload!==args[2])throw Error('Invalid BGM patch');record.playback.patch(args[1],bytes,frame);this.musicPatchBytes+=payload;continue;}
      if(op===0x303){const record=this.music.get(args[0]);if(!record||count!==2||payload!==args[1]*8)throw Error('Invalid BGM notification event');const table=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);this.setNotifications(record,Array.from({length:args[1]},(_,i)=>table.getUint32(i*8,true)),Array.from({length:args[1]},(_,i)=>table.getUint32(i*8+4,true)),frame);continue;}
      if(![0x48,0x34,0x40,0x3c,0x30].includes(op))continue;
      const expected=args.at(-1)>>>0;
      if(expected<0x80000000){const music=this.music.get(args[0]),sound=this.buffers.get(args[0]);if(!music&&!sound)throw Error('Unknown audio buffer');const hr=music?this.musicCall(music,op,args.slice(1,-1),frame):sound.playback.call(op,args.slice(1,-1),frame);if(hr!==expected)throw Error('Audio HRESULT differs');}++this.driverCalls;
    }
    c.campaign_audio_clear_events();
  }
  stop(){if(this.disposed||!this.initialized)return;super.stop();const frame=this.currentFrame();for(const record of this.music.values())this.musicCall(record,0x48,[],frame);}
  dispose(){if(this.disposed)return;this.disposed=true;this.initializationAbort.abort();super.dispose();for(const record of [...this.music.values(),...this.retired]){record.clock.dispose();record.playback.dispose();}this.music.clear();this.retired.clear();this.silent.disconnect();this.orderedMixer?.dispose();}
}
