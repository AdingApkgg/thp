"""Aggregate representative Standard natural recordings and complete replays.

Four character/shot profiles span Easy/Normal/Hard/Lunatic, plus ReimuA Extra.
This is not a fresh Standard4x4 natural-clear matrix or native every-frame,
GPU/audio/task equivalence. Recording and current replay snapshots stay separate.
All available raw actor archives are authenticated against recorded pool hashes.
"""
import hashlib,json,zlib
from pathlib import Path
from th06nc_native import ROOT

def main():
 sha=lambda b:hashlib.sha256(b).hexdigest()
 read=lambda p:json.loads((ROOT/p).read_bytes())
 plans=[(0,'reimu-a',1,'normal'),(1,'reimu-b',2,'hard'),(2,'marisa-a',0,'easy'),(3,'marisa-b',3,'lunatic'),(0,'reimu-a',4,'extra')]
 rows=[];source=None;archiveCount=0
 codecs={kind:read('docs/porting/th06nc-'+kind+'-browser-files-native-verified.json')for kind in ['score','replay']}
 for report in codecs.values():assert report['passed']is True
 for profile,name,difficulty,label in plans:
  home=f'extra-natural-{name}-standard-browser'if difficulty==4 else f'natural-run-{name}-difficulty{difficulty}-standard-browser'
  recordPath=f'docs/porting/th06nc-{home}-verified.json';playbackPath=f'docs/porting/th06nc-natural-playback-{name}-{label}-standard-browser-verified.json'
  record,playback=read(recordPath),read(playbackPath);assert record['passed']is True and playback['passed']is True
  assert record['profile']==playback['profile']==profile and playback['difficulty']==difficulty
  stages=[7]if difficulty==4 else list(range(1,6 if difficulty==0 else 7));assert playback['visited']==stages
  assert playback['checked']==len(record['checkpoints'])>0
  assert playback['goldenSourceSha256']==record['sourceSha256']
  if source is None:source=playback['sourceSha256']
  assert playback['sourceSha256']==source
  ending=next(e for e in record['evidence']if e['phase']in ['score-entry','result-summary']);assert ending['cleared']and ending['continuesUsed']==0
  assert ending['score']==playback['expectedScore']
  final=playback['evidence'][-1];assert final['phase']=='title'and final['titleState']==20 and final['score']==ending['score']
  assert final['save']['scoreBytes']==0 and final['save']['achievements']['unlocked']==[]and final['save']['achievements']['pending']==[]
  files={}
  for kind,file in [('score','score.dat'),('replay','natural-th6_01.rpy')]:
   path=f'artifacts/th06nc/{home}/{file}';raw=(ROOT/path).read_bytes();digest=sha(raw);assert any(e['path']==path and e['sha256']==digest and e['bytes']==len(raw)for e in codecs[kind]['files']),path
   files[kind]=dict(path=path,bytes=len(raw),sha256=digest)
  assert files['replay']['sha256']==playback['inputSha256']
  layout=record.get('poolSnapshotLayout');snapshots=record.get('poolSnapshots',[])
  if snapshots:
   assert [e['name']for e in layout]==['player','enemies','effects','bullets','lasers','items','popups'];total=sum(e['bytes']for e in layout);assert total<=32*1024*1024
   checkpoints={(c['stage'],c['frame']):c for c in record['checkpoints']};assert len(checkpoints)==len(record['checkpoints'])==len(snapshots)
   for snapshot in snapshots:
    path=Path(snapshot['file']);assert len(path.parts)==2 and path.parts[0]=='pool-snapshots'and path.suffix=='.gz'
    compressed=(ROOT/'artifacts/th06nc'/home/path).read_bytes();assert sha(compressed)==snapshot['sha256'];decoder=zlib.decompressobj(16+zlib.MAX_WBITS);raw=decoder.decompress(compressed,total+1);assert len(raw)==total and decoder.eof and not decoder.unconsumed_tail and not decoder.unused_data
    cursor=0;hashes=[]
    for pool in layout:
     end=cursor+pool['bytes'];hashes.append(sha(raw[cursor:end]));cursor=end
    assert hashes==checkpoints[(snapshot['stage'],snapshot['frame'])]['components'];archiveCount+=1
  rows.append(dict(profile=profile,difficulty=difficulty,stages=stages,score=ending['score'],deaths=ending['deathCount'],continues=ending['continuesUsed'],checkpoints=playback['checked'],actorArchives=len(snapshots),files=files,recordReport=recordPath,recordReportSha256=sha((ROOT/recordPath).read_bytes()),playbackReport=playbackPath,playbackReportSha256=sha((ROOT/playbackPath).read_bytes()),changedRecordingSources=playback['changedSources']))
 for path,digest in source.items():assert sha((ROOT/path).read_bytes())==digest,path
 report=dict(scope=__doc__,runs=rows,checkpoints=sum(r['checkpoints']for r in rows),authenticatedActorArchives=archiveCount,sourceSha256=source,passed=True,completeGame=False,nativeEquivalent=False)
 (ROOT/'docs/porting/th06nc-standard-natural-coverage-browser-verified.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(dict(passed=True,runs=len(rows),checkpoints=report['checkpoints'],authenticatedActorArchives=archiveCount)))
if __name__=='__main__':main()
