//The AudioWorklet owns mutable PCM while playing. Commands carry context-frame
//timestamps, and every render quantum reports cursors and crossed notices.
export class MusicRingWebPlaybackV3 {
  static async create(context,{format,pcm,notifications=[],commands=[],destination=context.destination}){
    const v=new DataView(format.buffer,format.byteOffset,format.byteLength),tag=v.getUint16(0,true),channels=v.getUint16(2,true),rate=v.getUint32(4,true),bits=v.getUint16(14,true),align=v.getUint16(12,true);
    if(tag!==1||rate!==context.sampleRate||![1,2].includes(channels)||![8,16].includes(bits)||align!==channels*bits/8||pcm.length%align)throw Error('Music worklet requires supported same-rate PCM');
    await context.audioWorklet.addModule(new URL('./MusicRingProcessorV3.mjs',import.meta.url));const node=new AudioWorkletNode(context,'th143-music-ring-v3',{numberOfInputs:0,numberOfOutputs:1,outputChannelCount:[2],processorOptions:{channels,bits,rate,pcm:new Uint8Array(pcm),notifications,commands}});const playback=new MusicRingWebPlaybackV3(context,node);node.connect(destination);return playback;
  }
  constructor(context,node){this.context=context;this.node=node;this.serial=1000000;this.state={frame:0,position:0,playing:false,loop:false,applied:0,lateCommands:0};this.notices=[];this.noticeCount=0;this.onDisposed=null;this.error=null;node.onprocessorerror=()=>{this.error=Error('Music ring processor failed');};node.port.onmessage=event=>{this.state=event.data;this.noticeCount+=event.data.notifications.length;this.notices.push(...event.data.notifications);if(this.notices.length>512)this.notices.splice(0,this.notices.length-512);if(event.data.disposed&&this.onDisposed){const done=this.onDisposed;this.onDisposed=null;this.dispose();done();}};}
  currentFrame(){return Math.round(this.context.currentTime*this.context.sampleRate);}
  send(op,args={},frame=this.currentFrame()){if(this.error)throw this.error;if(!Number.isSafeInteger(frame)||frame<0)throw Error('Invalid music command frame');this.node.port.postMessage({...args,op,frame,serial:this.serial++});}
  patch(offset,bytes,frame=this.currentFrame()){this.send('patch',{offset,bytes:new Uint8Array(bytes)},frame);}
  play(loop=true,frame=this.currentFrame()){this.send('play',{loop},frame);}
  stop(frame=this.currentFrame()){this.send('stop',{},frame);}
  setPosition(bytes,frame=this.currentFrame()){this.send('position',{bytes},frame);}
  setVolume(value,frame=this.currentFrame()){this.send('volume',{value},frame);}
  setPan(value,frame=this.currentFrame()){this.send('pan',{value},frame);}
  setNotifications(offsets,frame=this.currentFrame()){this.send('notifications',{offsets:[...offsets]},frame);}
  retire(frame,done){this.onDisposed=done;this.send('dispose',{},frame);}
  drainNotifications(){const result=this.notices;this.notices=[];return result;}
  dispose(){this.node.disconnect();this.node.port.close();}
}
