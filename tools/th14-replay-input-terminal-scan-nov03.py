"""Scan independently decoded TH14 replay input frames; do not infer original playback."""
from pathlib import Path
import argparse,hashlib,json,struct
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/replay-candidates-second-nov03';sha=lambda b:hashlib.sha256(b).hexdigest();codec=json.loads((H/'native-codec-verified.json').read_bytes());assert codec['passed'] and codec['files']==2
rows=[]
for name in ['th14_ud07c1','th14_ud0552']:
 m=json.loads((H/(name+'-source.json')).read_bytes());data=(H/(name+'-decoded.bin')).read_bytes();rpy=(H/(name+'.rpy')).read_bytes();assert m['actualNativeCodecVerified'] and sha(data)==m['decodedSha256'] and sha(rpy)==m['sha256'] and [x['stage'] for x in m['stages']]==[1,2,3,4,5,6]
 count,character,subtype,difficulty=struct.unpack_from('<4I',data,0x78);assert count==6 and [character,subtype,difficulty]==m['expectedSelection']
 row=next(x for x in codec['rows'] if x['name']==name);assert row['sha256']==m['sha256'] and row['decodedSha256']==m['decodedSha256'] and row['nativeCodecObserverSha256']==sha((H/'decode-native.py').read_bytes())
 offset=0x94;stages=[]
 for stage in m['stages']:
  number,seed=struct.unpack_from('<HH',data,offset);frames,payload=struct.unpack_from('<II',data,offset+4);assert number==stage['stage'] and frames==stage['frames'] and payload==stage['payloadBytes'] and frames*6<=payload
  start=offset+0xdc;assert start+payload<=len(data);markers=[i for i in range(frames) if data[start+6*i:start+6*i+6]==b'\xff'*6]
  stages.append(dict(stage=number,recordedInputFrames=frames,terminalMarkerCount=len(markers),terminalMarkerPositions=markers,lastInputSha256=sha(data[start+6*(frames-1):start+6*frames]) if frames else None));offset=start+payload
 assert offset==len(data) and all(x['terminalMarkerCount']==0 for x in stages)
 rows.append(dict(name=name,selection=m['expectedSelection'],sourceReplaySha256=sha(rpy),decodedSha256=sha(data),stages=stages))
result=dict(verifiedDecodedStageInputScan=True,files=2,stages=12,terminalMarkers=0,sourceReplayEofProved=False,actualOriginalPlaybackInferred=False,fullGameplayEquivalent=False,completeGame=False,nativeEquivalent=False,rows=rows,codecEvidenceSha256=sha((H/'native-codec-verified.json').read_bytes()),verifierSha256=sha(Path(__file__).read_bytes()))
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');p.add_argument('--output',type=Path,default=H/'terminal-input-scan.json');a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(H) or out.is_relative_to(R/'docs/porting');data=(json.dumps(result,indent=2)+'\n').encode()
if a.check:assert out.read_bytes()==data
else:out.write_bytes(data)
print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
