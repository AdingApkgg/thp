"""Revalidate historical natural Challenge recordings on the current runtime.
The recording source snapshots are retained separately. Current playback must
match every stored raw-pool/counter/RNG checkpoint and final score, then return
naturally without writing score/replay/achievements. This does not claim a fresh
current-runtime recording or native every-frame/GPU/task equivalence.
"""
import hashlib,json,sys
from th06nc_native import ROOT

def main():
 rows=[];source=None
 for profile,name in enumerate(['reimu-a','reimu-b','marisa-a','marisa-b']):
  for difficulty,label in enumerate((['easy','normal','hard','lunatic']if '--ordinary-only'in sys.argv else ['easy','normal','hard','lunatic','extra'])):
   recordHome=f'extra-natural-{name}-challenge-browser'if difficulty==4 else f'natural-run-{name}-difficulty{difficulty}-challenge-browser'
   recordPath=ROOT/'docs/porting'/f'th06nc-{recordHome}-verified.json'
   playbackPath=ROOT/'docs/porting'/f'th06nc-natural-playback-{name}-{label}-browser-verified.json'
   record=json.loads(recordPath.read_bytes());playback=json.loads(playbackPath.read_bytes());assert record['passed']and playback['passed'];assert playback['revalidateSource']is True
   assert playback['profile']==profile and playback['difficulty']==difficulty
   assert playback['visited']==([7]if difficulty==4 else list(range(1,6 if difficulty==0 else 7)));assert playback['checked']==len(record['checkpoints'])>0
   assert playback['goldenSourceSha256']==record['sourceSha256']
   expectedChanges=sorted(p for p in set(record['sourceSha256'])|set(playback['sourceSha256'])if record['sourceSha256'].get(p)!=playback['sourceSha256'].get(p));assert sorted(playback['changedSources'])==expectedChanges
   if source is None:source=playback['sourceSha256']
   assert source==playback['sourceSha256']
   replay=ROOT/'artifacts/th06nc'/recordHome/'natural-th6_01.rpy';assert hashlib.sha256(replay.read_bytes()).hexdigest()==playback['inputSha256']
   final=playback['evidence'][-1];assert final['phase']=='title'and final['titleState']==20;assert final['save']['scoreBytes']==0;assert final['save']['achievements']['unlocked']==[]and final['save']['achievements']['pending']==[]
   rows.append(dict(profile=profile,name=name,difficulty=difficulty,checkpoints=playback['checked'],score=playback['expectedScore'],changedSources=expectedChanges,recordReport=recordPath.relative_to(ROOT).as_posix(),recordReportSha256=hashlib.sha256(recordPath.read_bytes()).hexdigest(),playbackReport=playbackPath.relative_to(ROOT).as_posix(),playbackReportSha256=hashlib.sha256(playbackPath.read_bytes()).hexdigest(),replaySha256=playback['inputSha256']))
 for p,h in source.items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
 report=dict(scope=__doc__,profiles=rows,checkpoints=sum(r['checkpoints']for r in rows),sourceSha256=source,passed=True,completeGame=False,nativeEquivalent=False)
 (ROOT/'docs/porting'/('th06nc-challenge-revalidation-ordinary-matrix-browser-verified.json'if '--ordinary-only'in sys.argv else 'th06nc-challenge-revalidation-matrix-browser-verified.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,runs=len(rows),checkpoints=report['checkpoints'])))
if __name__=='__main__':main()
