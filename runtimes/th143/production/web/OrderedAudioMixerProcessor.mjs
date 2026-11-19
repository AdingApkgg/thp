//A fixed slot order prevents graph connection/processing order from choosing
//the floating addition order. This is a software renderer, not a native mixer.
class Th143OrderedAudioMixer extends AudioWorkletProcessor {
  constructor(options){super();this.slots=options.processorOptions.slots;this.blocks=0;if(!Number.isInteger(this.slots)||this.slots<1||this.slots>128)throw Error('Invalid mixer slot count');}
  process(inputs,outputs){
    const output=outputs[0];if(output.length!==2)throw Error('Ordered mixer requires stereo output');const frames=output[0].length;
    for(let i=0;i<frames;++i){let left=0,right=0;for(let slot=0;slot<this.slots;++slot){const input=inputs[slot];if(input?.length){left+=input[0][i];right+=(input[1]||input[0])[i];}}output[0][i]=left;output[1][i]=right;}
    this.port.postMessage({frame:currentFrame+frames,blocks:++this.blocks,slots:this.slots});return true;
  }
}
registerProcessor('th143-ordered-audio-mixer-v1',Th143OrderedAudioMixer);
