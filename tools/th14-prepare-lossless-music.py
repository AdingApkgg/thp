"""Extract original TH14 PCM into byte-verified lossless FLAC;retain old OGG."""
import hashlib,json,struct
from pathlib import Path
import numpy as np
import soundfile as sf
ROOT=Path(__file__).resolve().parents[1]
def main():
 archive=json.loads((ROOT/'artifacts/archive-differential/th14.json').read_text(encoding='utf8'))
 formats=(Path(archive['extraction'])/'thbgm.fmt').read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest()
 assert sha(formats)==next(r['sha256'] for r in archive['decoded'] if r['name']=='thbgm.fmt')
 target=json.loads((ROOT/'runtimes/th14/target.json').read_text(encoding='utf8'));path=Path(target['dataArchives']['thbgm.dat']['path']);assert path.stat().st_size==target['dataArchives']['thbgm.dat']['bytes']
 out=ROOT/'runtimes/th14/th14_web/assets/sdl-native';rows=[]
 with path.open('rb') as source:
  assert source.read(4)==b'ZWAV';source.seek(0);archive_hash=hashlib.file_digest(source,'sha256').hexdigest()
  for n in range(18):
   name,offset,preload,intro,length=struct.unpack_from('<16sIIII',formats,n*52);stem=name.split(b'\0')[0].decode('ascii').removesuffix('.wav')
   tag,channels,rate,byte_rate,align,bits=struct.unpack_from('<HHIIHH',formats,n*52+32)
   assert (tag,channels,bits,align)==(1,2,16,4) and byte_rate==rate*align and intro%align==0 and length%align==0 and 0<=intro<length and offset+length<=path.stat().st_size
   if n<17:assert offset+length==struct.unpack_from('<I',formats,(n+1)*52+16)[0]
   source.seek(offset);pcm=source.read(length);assert len(pcm)==length;samples=np.frombuffer(pcm,dtype='<i2').reshape(-1,channels);dest=out/'music'/(stem+'.flac')
   if not dest.exists():
    pending=dest.with_suffix('.flac.tmp')
    with sf.SoundFile(str(pending),'w',samplerate=rate,channels=channels,subtype='PCM_16',format='FLAC',compression_level=1.) as f:
     for at in range(0,len(samples),65536):f.write(samples[at:at+65536])
    pending.replace(dest)
   decoded,decoded_rate=sf.read(str(dest),dtype='int16',always_2d=True);decoded_bytes=decoded.astype('<i2',copy=False).tobytes();assert decoded.shape==samples.shape and decoded_rate==rate and decoded_bytes==pcm
   rows.append(dict(name=stem+'.wav',file=dest.name,frames=len(samples),loopFrame=intro//align,rate=rate,channels=channels,encodedBytes=dest.stat().st_size,pcmSha256=sha(pcm),decodedPcmSha256=sha(decoded_bytes),encodedSha256=sha(dest.read_bytes()),codec='flac',lossless=True))
   print(f'{n+1}/18 {stem}: exact {len(samples)} frames, {dest.stat().st_size} bytes',flush=True)
 (out/'music-lossless-verification.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf8')
 active=out/'music-verification.json';backup=ROOT/'artifacts/th14/music-vorbis-verification-oct11.json'
 if active.exists() and any(not r.get('lossless',False) for r in json.loads(active.read_text(encoding='utf8'))) and not backup.exists():backup.write_bytes(active.read_bytes())
 active.write_text(json.dumps(rows,indent=2)+'\n',encoding='utf8')
 proof=dict(passed=True,tracks=len(rows),sourceArchiveSha256=archive_hash,formatSha256=sha(formats),pcmBytes=sum(r['frames']*4 for r in rows),encodedBytes=sum(r['encodedBytes'] for r in rows),tracksVerified=rows,toolSha256=sha(Path(__file__).read_bytes()),scope='Original local thbgm.dat PCM to FLAC: all 18 tracks decode byte-identically, with original frame count/rate/channels/loop frame. Active local music catalog uses FLAC;existing OGG files retained. No playback/mixer/DirectSound/thread equivalence claim.')
 (ROOT/'docs/porting/th14-music-lossless-verified.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf8');print(f'PASS {len(rows)} byte-identical original FLAC tracks')
if __name__=='__main__':main()
