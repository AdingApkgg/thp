"""Verify actual retained bytes; no resynchronization or expected-state injection."""
import argparse, hashlib, json
from pathlib import Path

R=Path(__file__).resolve().parents[1]
A=R/'artifacts/th14'
DEST=R/'docs/porting/th14-dialogue-section-observed-oct20.json'

def main():
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');p.add_argument('--check',action='store_true');args=p.parse_args();assert args.write != args.check
 bindings={}
 def read(path):
  path=Path(path);data=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest());return data
 def load(path):return json.loads(read(path))
 native=load(A/'dialogue-section-native-v2-oct20/report.json')
 assert native['executableSha256']=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
 producer=read(A/'dialogue-section-native-v2-oct20.py');assert hashlib.sha256(producer).hexdigest()==native['toolSha256']
 assert native['cases']==12 and len(native['rows'])==12
 assert all(r['sectionBefore']==r['sectionAfter'] and not r['sectionWrites'] and r['ownerCleared'] and r['nameScripts']==[159 if r['sectionBefore']>=5 else 158] for r in native['rows'])
 core=load(A/'dialogue-section-candidate-core-oct20/build-result.json');assert core['engineObjects']==141 and core['sourceChanges']==['cpp/game/GameBattle.cpp']
 for name,h in core['sourceHashes'].items():
  data=read(A/'dialogue-section-candidate-core-oct20/source'/name);assert hashlib.sha256(data).hexdigest()==h,name
  workspace=read(R/'runtimes/th12/th12_web'/name)
  expected='a291010053963e25dadef2be15ddb3c217110cd2377fc495402ef375150f8c45' if name=='cpp/game/ResourceCrypt.cpp' else h
  assert hashlib.sha256(workspace).hexdigest()==expected,name
 for row in core['outputs']:assert hashlib.sha256(read(row['path'])).hexdigest()==row['sha256']
 probe=load(A/'dialogue-section-candidate-playback-oct20/build.json');assert hashlib.sha256(read(A/'dialogue-section-candidate-playback-oct20/probe.wasm')).hexdigest()==probe['wasmSha256']
 for path,h in probe['fixtureDependencyHashes'].items():assert hashlib.sha256(read(path)).hexdigest()==h
 batch=load(A/'dialogue-section-candidate-playback-oct20/batch-completed.json');assert batch['allCasesExecuted'] and len(batch['cases'])==30
 cases=[];total=0
 for case in batch['cases']:
  key=case['key'];new=A/'dialogue-section-candidate-playback-oct20/playbacks'/key;old=A/'dialogue-damage-candidate-playback-oct18/playbacks'/key
  c,b=load(new/'receipt.json'),load(old/'receipt.json')
  assert not c['error'] and not c['frameBudgetReached'] and c['skipped']==c['unsupported']==0
  assert c['replaySha256']==b['replaySha256'] and c['archiveSha256']==b['archiveSha256']
  for n in ('callbacks','phase','stage','currentQueueFullPlaybackVerified','gameOverRequested'):assert c[n]==b[n],(key,n)
  for name in ('selected-state.u32','callback-active.u8','enemy-owner.u8','queue.json'):assert read(new/name)==read(old/name),(key,name)
  assert len(read(new/'selected-state.u32'))==c['callbacks']*128
  hud=load(new/'hud-events.json')
  main=[r for r in hud if r['stage']==6 and 85<=r['spellId']<=108 and r['nameScript']!=0xffffffff]
  assert all(r['section']==6 and r['nameScript']==159 and r['nameSprite']==110 for r in main),key
  cases.append(dict(key=key,callbacks=c['callbacks'],naturalReplayEof=c['currentQueueFullPlaybackVerified'],gameOver=c['gameOverRequested'],fullRaw32ActivityOwnerQueueEqual=True,mainBossNameEvents=len(main)))
  total+=c['callbacks']
 assert total==2885731 and sum(r['naturalReplayEof'] for r in cases)==28 and sum(r['gameOver'] for r in cases)==2
 sdl=load(A/'dialogue-section-sdl-oct20/build.json');assert sdl['compiled'] and len(sdl['objectHashes'])==146 and sdl['importsUnchanged'] and sdl['exportsUnchanged']
 for group in ('sourceHashes','headerHashes'):
  for name,h in sdl[group].items():assert hashlib.sha256(read(A/'dialogue-section-sdl-oct20/source'/name)).hexdigest()==h
 for name,h in sdl['objectHashes'].items():assert hashlib.sha256(read(A/'dialogue-section-sdl-oct20'/name)).hexdigest()==h
 assert hashlib.sha256(read(A/'dialogue-section-sdl-oct20/th11.wasm')).hexdigest()==sdl['wasmSha256']
 read(Path(__file__))
 report=dict(passed=True,originalCleanupCases=12,coreObjects=141,sdlObjects=146,fullReplayCases=30,totalCallbacks=total,naturalReplayEofCases=28,gameOverCases=2,allRaw32ActivityOwnerQueueBytesUnchanged=True,cases=cases,wasmSha256=sdl['wasmSha256'],bindings=bindings,completeGame=False,nativeEquivalent=False,scope='Actual original terminal opcode0 and owner destruction retain section, then separately invoked full4350b0 selects name. Controlled null ANM lookup/free and name allocation/binding/first update/registration; no full original world or actual native UI lifecycle claim. Candidate headless30 complete physical inputs compared with frozen published gameplay; real resource queues and RecordingGraphics/no-target retirement, no real GPU/audio. Root unrelated ResourceCrypt edit retained and excluded from frozen builds. No full-game1:1 claim.')
 data=(json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode()
 if args.write:
  assert not DEST.exists();DEST.write_bytes(data)
 else:assert DEST.read_bytes()==data,'Evidence changed'
 print('PASS',len(bindings),'bindings;',total,'callbacks;30 raw streams unchanged;28EOF/2GameOver')

if __name__=='__main__':main()
