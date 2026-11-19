//Physical ring playback prototype. Same-rate PCM only. Device timing,
//resampling and DirectSound notification latency remain separate proof gaps.
class Th143MusicRingProcessor extends AudioWorkletProcessor {
  constructor(options){
    super();const p=options.processorOptions||{};this.channels=p.channels;this.bits=p.bits;this.align=this.channels*this.bits/8;this.pcm=new Uint8Array(p.pcm);this.view=new DataView(this.pcm.buffer);this.frames=this.pcm.length/this.align;
    if(![1,2].includes(this.channels)||![8,16].includes(this.bits)||p.rate!==sampleRate||!Number.isInteger(this.frames)||this.frames<1)throw Error('Unsupported music ring format');
    this.position=0;this.playing=false;this.loop=false;this.volume=0;this.pan=0;this.left=1;this.right=1;this.lateCommands=0;this.applied=0;this.commands=[];this.notifications=p.notifications||[];this.disposed=false;
    for(const command of p.commands||[])this.enqueue(command);this.port.onmessage=event=>this.enqueue(event.data);
  }
  enqueue(command){
    if(!Number.isSafeInteger(command.frame)||command.frame<0||!Number.isSafeInteger(command.serial))throw Error('Invalid ring command timestamp');
    this.commands.push(command);this.commands.sort((a,b)=>a.frame-b.frame||a.serial-b.serial);
  }
  apply(c,frame){
    if(c.frame<frame)++this.lateCommands;++this.applied;
    if(c.op==='patch'){const bytes=new Uint8Array(c.bytes);if(!Number.isInteger(c.offset)||c.offset<0||c.offset+bytes.length>this.pcm.length)throw Error('Invalid PCM patch');this.pcm.set(bytes,c.offset);}
    else if(c.op==='play'){this.loop=!!c.loop;this.playing=true;}
    else if(c.op==='stop')this.playing=false;
    else if(c.op==='position'){if(!Number.isInteger(c.bytes)||c.bytes<0||c.bytes>=this.pcm.length)throw Error('Invalid ring position');this.position=Math.floor(c.bytes/this.align);}
    else if(c.op==='volume'||c.op==='pan'){const max=c.op==='pan'?10000:0;if(!Number.isInteger(c.value)||c.value< -10000||c.value>max)throw Error('Invalid ring gain');this[c.op]=c.value;this.left=10**((this.volume-Math.max(this.pan,0))/2000);this.right=10**((this.volume+Math.min(this.pan,0))/2000);}
    else if(c.op==='notifications'){if(!Array.isArray(c.offsets)||c.offsets.length>64||c.offsets.some(v=>!Number.isInteger(v)||v<0||v>=this.pcm.length))throw Error('Invalid notification offsets');this.notifications=c.offsets.slice();}
    else if(c.op==='dispose'){this.playing=false;this.disposed=true;}
    else throw Error('Unsupported ring command');
  }
  sample(frame,channel){const at=(frame*this.channels+Math.min(channel,this.channels-1))*this.bits/8;return this.bits===8?(this.pcm[at]-128)/128:this.view.getInt16(at,true)/32768;}
  process(inputs,outputs){
    const output=outputs[0];if(!output?.length)return !this.disposed;const count=output[0].length,notices=[];
    for(let i=0;i<count;++i){const frame=currentFrame+i;while(this.commands.length&&this.commands[0].frame<=frame)this.apply(this.commands.shift(),frame);
      if(this.playing){output[0][i]=this.sample(this.position,0)*this.left;if(output[1])output[1][i]=this.sample(this.position,1)*this.right;const last=(this.position+1)*this.align-1;for(const offset of this.notifications)if(offset===last)notices.push({frame:frame+1,offset});++this.position;if(this.position===this.frames){if(this.loop)this.position=0;else{this.position=0;this.playing=false;}}}
      else for(const channel of output)channel[i]=0;
    }
    this.port.postMessage({frame:currentFrame+count,position:this.position*this.align,playing:this.playing,loop:this.loop,applied:this.applied,lateCommands:this.lateCommands,disposed:this.disposed,notifications:notices});return !this.disposed;
  }
}
registerProcessor('th143-music-ring-v3',Th143MusicRingProcessor);
