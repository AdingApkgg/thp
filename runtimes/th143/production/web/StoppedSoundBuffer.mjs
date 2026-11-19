// Stopped secondary-buffer storage and properties for the browser audio host.
// This component does not implement playback, an audio clock, or a mixer.
export const SoundHresult = Object.freeze({ok:0, invalid:0x80070057, controlUnavailable:0x8878001e});
const validWord = n => Number.isInteger(n) && n >= 0 && n <= 0xffffffff;
export class StoppedSoundBuffer {
  #storage;
  #volume=0;
  #pan=0;
  #position=0;
  constructor(format, pcm, sharedStorage=null) {
    if(sharedStorage) { this.#storage=sharedStorage;return; }
    if(!(format instanceof Uint8Array)||format.length!==18||!(pcm instanceof Uint8Array))throw new TypeError('Expected literal WAVEFORMATEX and PCM bytes');
    const f=new DataView(format.buffer,format.byteOffset,format.byteLength),channels=f.getUint16(2,true),rate=f.getUint32(4,true),align=f.getUint16(12,true),bits=f.getUint16(14,true);
    if(f.getUint16(0,true)!==1||![1,2].includes(channels)||![8,16].includes(bits)||![22050,44100].includes(rate)||align!==channels*bits/8||f.getUint32(8,true)!==rate*align||!pcm.length||pcm.length%align)throw new RangeError('Unsupported PCM sound buffer');
    const normalized=new Uint8Array(format);normalized[16]=normalized[17]=0;
    this.#storage={format:normalized,data:new Uint8Array(pcm),channels,rate,align,bits};
  }
  get byteLength(){return this.#storage.data.length;}
  get blockAlign(){return this.#storage.align;}
  get channels(){return this.#storage.channels;}
  get sampleRate(){return this.#storage.rate;}
  get bitsPerSample(){return this.#storage.bits;}
  get volume(){return this.#volume;}
  get pan(){return this.#pan;}
  get position(){return this.#position;}
  duplicate(){const b=new StoppedSoundBuffer(null,null,this.#storage);b.#volume=this.#volume;b.#pan=this.#pan;return b;}
  readBytes(){return new Uint8Array(this.#storage.data);}
  writeBytes(offset,bytes){
    if(!validWord(offset)||!(bytes instanceof Uint8Array)||offset+bytes.length>this.byteLength)return SoundHresult.invalid;
    this.#storage.data.set(bytes,offset);return SoundHresult.ok;
  }
  getFormat(capacity){
    if(capacity===0)return {hr:0,written:18,data:new Uint8Array()};
    if(!validWord(capacity)||capacity<18)return {hr:SoundHresult.invalid,written:0,data:new Uint8Array()};
    return {hr:0,written:18,data:new Uint8Array(this.#storage.format)};
  }
  setVolume(value){value|=0;if(value < -10000 || value > 0)return SoundHresult.invalid;this.#volume=value;return 0;}
  setPan(value){value|=0;if(value < -10000 || value > 10000)return SoundHresult.invalid;this.#pan=value;return 0;}
  setPosition(value){
    if(!validWord(value)||value>=this.byteLength)return SoundHresult.invalid;
    this.#position=value-value%this.blockAlign;return 0;
  }
  snapshot(){return {volumeHr:0,volume:this.#volume,panHr:0,pan:this.#pan,frequencyHr:SoundHresult.controlUnavailable,frequency:0,statusHr:0,status:0,positionHr:0,play:this.#position,write:this.#position};}
}
