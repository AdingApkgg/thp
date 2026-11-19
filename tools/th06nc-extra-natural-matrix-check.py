"""Aggregate current-source natural Extra Challenge clears and complete playbacks."""
import hashlib,json
from th06nc_native import ROOT

def main():
 rows=[];source=None
 for profile,name in enumerate(['reimu-a','reimu-b','marisa-a','marisa-b']):
  recordPath=ROOT/'docs/porting'/f'th06nc-extra-natural-{name}-challenge-browser-verified.json'
  playbackPath=ROOT/'docs/porting'/f'th06nc-natural-playback-{name}-extra-browser-verified.json'
  record=json.loads(recordPath.read_bytes());playback=json.loads(playbackPath.read_bytes())
  assert record['passed']and playback['passed']
  assert record['profile']==playback['profile']==profile
  assert playback['visited']==[7]
  assert playback['checked']==len(record['checkpoints'])>0
  assert record['sourceSha256']==playback['sourceSha256']
  if source is None:source=record['sourceSha256']
  assert source==record['sourceSha256']
  assert record['evidence'][0]['profile']['mode']==1
  clear=next(e for e in record['evidence']if e['cleared'])
  assert clear['continuesUsed']==0
  assert clear['score']==playback['expectedScore']
  home=ROOT/'artifacts/th06nc'/f'extra-natural-{name}-challenge-browser'
  replay=home/'natural-th6_01.rpy';score=home/'score.dat'
  rows.append(dict(profile=profile,name=name,frame=clear['frame'],deaths=clear['deathCount'],score=clear['score'],checkpoints=playback['checked'],drawRequests=len(record['drawSchedule']),replaySha256=hashlib.sha256(replay.read_bytes()).hexdigest(),scoreSha256=hashlib.sha256(score.read_bytes()).hexdigest(),recordReport=recordPath.relative_to(ROOT).as_posix(),playbackReport=playbackPath.relative_to(ROOT).as_posix()))
 for path,sha in source.items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha,path
 report=dict(scope='Four ordinary title-selected Extra Challenge character/shot combinations after real keyboard secret unlock. Natural ECL/STD/MSG completion, result/save/reload and title-launched complete playback. Seven raw actor pools/counters/RNG checkpoints match at recorded draw cadence, final score matches and playback leaves score/replay files unchanged. Standard Extra, earned no-continue unlock, every-frame/native application/GPU/audio/task equivalence excluded.',profiles=rows,checkpoints=sum(row['checkpoints']for row in rows),sourceSha256=source,passed=True,completeGame=False,nativeEquivalent=False)
 (ROOT/'docs/porting/th06nc-extra-natural-matrix-browser-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(dict(passed=True,profiles=len(rows),checkpoints=report['checkpoints'])))
if __name__=='__main__':main()
