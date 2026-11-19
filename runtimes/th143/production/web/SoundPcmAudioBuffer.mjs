// Raw integer PCM conversion; no decodeAudioData codec/resampling stage.
export function decodeSoundPcm(buffer) {
  const pcm=buffer.readBytes(),bits=buffer.bitsPerSample,channels=buffer.channels,frames=pcm.length/buffer.blockAlign;
  const output=Array.from({length:channels},()=>new Float32Array(frames));
  const view=new DataView(pcm.buffer,pcm.byteOffset,pcm.byteLength);
  for(let frame=0;frame<frames;++frame)for(let channel=0;channel<channels;++channel){
    const sample=frame*channels+channel;
    output[channel][frame]=bits===8?(pcm[sample]-128)/128:view.getInt16(sample*2,true)/32768;
  }
  return output;
}
export function createSoundAudioBuffer(context,buffer) {
  const decoded=decodeSoundPcm(buffer),audio=context.createBuffer(buffer.channels,decoded[0].length,buffer.sampleRate);
  for(let channel=0;channel<decoded.length;++channel)audio.copyToChannel(decoded[channel],channel);
  return audio;
}
