"""Prepare TH14 lossless music by default; --lossy writes a separate legacy index."""
import hashlib,json,re,struct
from pathlib import Path
import numpy as np
import soundfile as sf
import importlib,sys
if '--lossy' not in sys.argv:
    importlib.import_module('th14-prepare-lossless-music').main()
    raise SystemExit(0)
ROOT=Path(__file__).resolve().parents[1]
archive=json.loads((ROOT/'artifacts/archive-differential/th14.json').read_text(encoding='utf-8'))
data=Path(archive['extraction'])
formats=(data/'thbgm.fmt').read_bytes()
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(formats)==next(r['sha256'] for r in archive['decoded'] if r['name']=='thbgm.fmt')
comments=re.findall(rb'@bgm/([A-Za-z0-9_]+)',(data/'musiccmt.txt').read_bytes())
names=[formats[n:n+16].split(b'\0')[0].decode('ascii').removesuffix('.wav') for n in range(0,len(formats)-51,52) if formats[n]]
expected=[s.decode() for s in comments]+[s for s in names if s.encode() not in comments]
catalog=(ROOT/'runtimes/th12/th12_web/cpp/game/MusicCatalog.hpp').read_text(encoding='utf-8')
actual=re.findall(r'\{\d+,"([^"]+)"\}',re.search(r'th14_music_tracks\[\]=\{(.*?)\};',catalog,re.S)[1])
assert actual==expected and len(names)==18 and len(comments)==17
target=json.loads((ROOT/'runtimes/th14/target.json').read_text(encoding='utf-8'))
source_path=Path(target['dataArchives']['thbgm.dat']['path'])
out=ROOT/'runtimes/th14/th14_web/assets/sdl-native';(out/'music').mkdir(parents=True,exist_ok=True)
report=[]
with source_path.open('rb') as source:
    assert source.read(4)==b'ZWAV'
    for n,stem in enumerate(names):
        name,offset,preload,intro,length=struct.unpack_from('<16sIIII',formats,n*52)
        format_tag,channels,rate,byte_rate,align,bits=struct.unpack_from('<HHIIHH',formats,n*52+32)
        assert format_tag==1 and channels==2 and bits==16 and align==4 and byte_rate==rate*align
        assert length%align==0 and intro%align==0 and 0<=intro<length and offset+length<=source_path.stat().st_size
        if n+1<len(names):assert offset+length==struct.unpack_from('<I',formats,(n+1)*52+16)[0]
        source.seek(offset);pcm=source.read(length);assert len(pcm)==length
        samples=np.frombuffer(pcm,dtype='<i2').reshape(-1,channels)
        path=out/'music'/(stem+'.ogg')
        if not path.exists() or sf.info(str(path)).frames!=len(samples):
            pending=path.with_suffix('.ogg.tmp')
            with sf.SoundFile(str(pending),'w',samplerate=rate,channels=channels,subtype='VORBIS',format='OGG',compression_level=.4) as dest:
                for at in range(0,len(samples),16384):dest.write(samples[at:at+16384].astype(np.float32)/32768.)
            pending.replace(path)
        decoded,decoded_rate=sf.read(str(path),dtype='int16',always_2d=True)
        assert decoded.shape==samples.shape and decoded_rate==rate
        report.append(dict(name=stem+'.wav',file=path.name,frames=len(samples),loopFrame=intro//align,rate=rate,channels=channels,
                           encodedBytes=path.stat().st_size,pcmSha256=sha(pcm),encodedSha256=sha(path.read_bytes()),codec='vorbis',lossless=False))
        print(f'{n+1}/18 {stem}: {len(samples)} frames, loop {intro//align}',flush=True)
# The TH14 production decoder opens FLAC. An optional legacy conversion must
# not replace the active resource list with incompatible OGG file names.
(out/'music-vorbis-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
proof=dict(passed=True,tracks=len(report),comments=len(comments),frames=sum(r['frames'] for r in report),formatSha256=sha(formats),
           musicOrder=expected,tracksVerified=report,scope='Local Vorbis conversion; decoded frame counts, sample rates, channels, loop boundaries and room cue mapping. Lossy encoding, not PCM equivalence.',toolSha256=sha(Path(__file__).read_bytes()))
(ROOT/'docs/porting/th14-music-verified.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(f'PASS: {len(report)} original TH14 music tracks, {proof["frames"]} decoded frames.')
