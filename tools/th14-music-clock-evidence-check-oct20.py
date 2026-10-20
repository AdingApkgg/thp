"""Independently recompare retained PCM and bind the adopted clock implementation."""
import argparse,hashlib,json,struct
from pathlib import Path
R=Path(__file__).resolve().parents[1];A=R/'artifacts/th14';D=R/'docs/porting/th14-music-clock-observed-oct20.json'

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--write',action='store_true');parser.add_argument('--check',action='store_true');args=parser.parse_args();assert args.write!=args.check
 bindings={}
 def read(path):
  path=Path(path);b=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest());return b
 def load(path):return json.loads(read(path))
 sha=lambda b:hashlib.sha256(b).hexdigest()
 native=load(A/'music-clock-native-v3-oct20/report.json');assert native['cases']==216 and native['tracks']==18
 assert sha(read(A/'music-clock-native-v3-oct20.py'))==native['toolSha256']
 assert native['executableSha256']=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
 target=load(R/'runtimes/th14/target.json');bgm=Path(target['dataArchives']['thbgm.dat']['path']);assert bgm.stat().st_size==397831536
 with bgm.open('rb') as stream:bgm_hash=hashlib.file_digest(stream,'sha256').hexdigest()
 lossless=load(R/'docs/porting/th14-music-lossless-verified.json');assert lossless['sourceArchiveSha256']==bgm_hash
 with bgm.open('rb') as stream:
  for row in native['rows']:
   pcm=read(A/'music-clock-native-v3-oct20'/row['pcmFile']);assert len(pcm)==row['pcmBytes'] and sha(pcm)==row['pcmSha256'];assert len(row['readCalls'])==1
   call=row['readCalls'][0];stream.seek(call['offset']);assert stream.read(call['bytes'])==pcm and sha(pcm)==call['sha256']
 candidate=A/'music-clock-candidate-v3-oct20';comparison=load(candidate/'comparison.json');legacy=load(candidate/'legacy-controls-v2.json');build=load(candidate/'build.json');prep=load(candidate/'prepared.json')
 assert comparison['cases']==comparison['exactCases']==180 and comparison['skippedZeroCases']==36 and comparison['comparedWords']==298224 and comparison['unequalWords']==0
 assert comparison['nativeReportSha256']==sha(read(A/'music-clock-native-v3-oct20/report.json'))
 assert sha(read(candidate/'probe.wasm'))==comparison['wasmSha256']==build['wasmSha256']
 for path,row in build['bindings'].items():
  b=read(path);assert len(b)==row['bytes'] and sha(b)==row['sha256']
 compared=0
 for row in comparison['rows']:
  actual=read(candidate/f"pcm/{row['index']:03d}-actual.f32");expected=read(candidate/f"pcm/{row['index']:03d}-retail.f32");n=native['rows'][row['index']]
  original=read(A/'music-clock-native-v3-oct20'/n['pcmFile']);words=struct.unpack('<'+'h'*(len(original)//2),original);normalized=struct.pack('<'+'f'*len(words),*(v/32768 for v in words))
  assert expected==normalized==actual and len(actual)==row['words']*4 and sha(actual)==row['actualSha256']==row['retailSha256'];compared+=row['words']
 assert compared==298224
 assert legacy['passed'] and legacy['cases']==37 and legacy['pausedMuteDiscardRetry'] and legacy['clockFrozenAtZero'] and not legacy['zeroTimeNativeEquivalent']
 baseline=load(A/'music-clock-portable-oct20/comparison-v3.json');assert baseline['cases']==18 and baseline['unequalWords']==34723
 baseline_differences=0
 with bgm.open('rb') as stream:
  for row in baseline['rows']:
   idx=row['track'];actual=read(A/f'music-clock-portable-oct20/track{idx:02d}-v3-actual.f32');expected=read(A/f'music-clock-portable-oct20/track{idx:02d}-v3-retail.f32');assert len(actual)==len(expected)==8192
   assert sha(actual)==row['actualSha256'] and sha(expected)==row['retailPcmSha256'];baseline_differences+=sum(x!=y for x,y in zip(struct.unpack('<2048I',actual),struct.unpack('<2048I',expected)))
   n=next(n for n in native['rows'] if n['track']==row['name'] and n['targetSeconds']==1.25 and n['pausedSeconds']==0);entry=bytes.fromhex(n['format']);offset=struct.unpack_from('<I',entry,16)[0];stream.seek(offset+55125*4);pcm=stream.read(4096);words=struct.unpack('<2048h',pcm);assert actual==struct.pack('<2048f',*(v/32768 for v in words))
 assert baseline_differences==34723
 sdl=load(A/'music-clock-sdl-oct20/build.json');assert sdl['compiled'] and len(sdl['objectHashes'])==146 and sdl['importsUnchanged'] and sdl['exportsUnchanged']
 for group in ('sourceHashes','headerHashes'):
  for name,h in sdl[group].items():assert sha(read(A/'music-clock-sdl-oct20/source'/name))==h
 for name,h in sdl['objectHashes'].items():assert sha(read(A/'music-clock-sdl-oct20'/name))==h
 assert sha(read(A/'music-clock-sdl-oct20/th11.wasm'))==sdl['wasmSha256']
 audio='runtimes/th12/th12_web/cpp/sdl/AudioDevice.cpp';assert sha(read(R/audio))==prep['sourceChanges']['th12_web/cpp/sdl/AudioDevice.cpp']==sdl['sourceHashes']['th12_web/cpp/sdl/AudioDevice.cpp']
 adoption=load(A/'music-clock-adoption-oct20/receipt.json')
 for row in adoption['files']:assert sha(read(R/row['path']))==row['sha256']
 read(Path(__file__))
 result=dict(passed=True,originalClockSeekReadCases=216,originalPositiveTimePcmCases=180,originalPositiveTimePcmWords=298224,positiveTimePcmDifferenceWords=0,baselineDeclared1250msCases=18,baselineDifferenceWords=34723,legacyFrozenClockCases=37,zeroTimeNativeEquivalent=False,zeroTimeRetainsPriorFallback=True,coreGameLogicChanged=False,sdlObjects=146,wasmSha256=sdl['wasmSha256'],sourceMusicArchiveSha256=bgm_hash,bindings=bindings,audioPlayed=False,completeGame=False,nativeEquivalent=False,scope='Actual original clock/wrap and bounded seek/read components; controlled QPC, Stop and read-only file services. Positive-time actual production mixer candidate PCM prefixes match normalized original reads under the same declared counter time, with pause and global suspension inputs. Whole DirectSound recreation/refill/device queue, audible output, actual Application Continue and zero/sub-frame raw-file underflow are not certified. Legacy37 checks retain the zero-clock decoder fallback and are separate from original equality.')
 data=(json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode()
 if args.write:assert not D.exists();D.write_bytes(data)
 else:assert D.read_bytes()==data,'Evidence changed'
 print('PASS',len(bindings),'bindings;180 positive-time PCM prefixes /298224 words exact;37 separate fallback controls')

if __name__=='__main__':main()
