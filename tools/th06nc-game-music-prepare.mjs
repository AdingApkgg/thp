import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {openPkgl} from '../shared/th06nc/pkgl.mjs';
import {readNativeOpus,nativeOpusToOgg} from '../shared/th06nc/opus-container.mjs';
import {readMusicLoop} from '../shared/th06nc/music-loop.mjs';
const sha=bytes=>createHash('sha256').update(bytes).digest('hex'),target=JSON.parse(readFileSync('runtimes/th06nc/target.json')),evidence=JSON.parse(readFileSync('docs/porting/th06nc-opus-native-verified.json')),raw=readFileSync(target.dataArchives['th06MD.dat'].path),archive=await openPkgl((offset,length)=>raw.subarray(offset,offset+length),raw.length,'th06MD.dat'),files=[];
for(const directory of ['bgm','bgm2']){
 mkdirSync('runtimes/th06nc/artifacts/audio/'+directory,{recursive:true});
 for(let index=1;index<=18;index++){
  const stem='th06_'+String(index).padStart(2,'0'),file=stem+'.opus',source=readFileSync('H:/Games/th/06nc/data/'+directory+'/'+file),expected=evidence.files.find(f=>f.directory===directory&&f.file===file);if(sha(source)!==expected?.sha256)throw Error('Music lacks native evidence '+directory+'/'+file);
  const stream=readNativeOpus(source),ogg=nativeOpusToOgg(stream),entry=archive.entries.find(e=>e.name===stem+(directory==='bgm2'?'o':'')+'.pos'),pos=await archive.readEntry(entry.index),loop=readMusicLoop(pos),[start,end]=loop.source;
  // Native 7be52..7bea4 converts 44.1 kHz positions to 48 kHz, truncating.
  const loopStart=loop.start,loopEnd=loop.end;if(loopStart<0||loopEnd<=loopStart)throw Error('Invalid native loop '+stem);
  writeFileSync('runtimes/th06nc/artifacts/audio/'+directory+'/'+stem+'.ogg',ogg);files.push({directory,file:stem+'.ogg',originalFile:file,originalSha256:sha(source),sha256:sha(ogg),bytes:ogg.length,channels:stream.channels,sampleRate:48000,samples:stream.samples,loopSource:[start,end],loopStart,loopEnd,loopMetadataSha256:sha(pos)});
 }
}
writeFileSync('runtimes/th06nc/artifacts/audio/music-manifest.json',JSON.stringify(files,null,2)+'\n');console.log(JSON.stringify({files:files.length,bytes:files.reduce((sum,file)=>sum+file.bytes,0)}));
