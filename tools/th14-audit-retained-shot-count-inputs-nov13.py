"""Inspect retained original shot-count counterexamples without new game runs."""
from pathlib import Path
from collections import defaultdict
import hashlib,json,struct
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/option-refresh-oracle-nov13';bindings={}
def raw(p):
 b=p.read_bytes();bindings[p.relative_to(R).as_posix()]=dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest());return b
def load(p):return json.loads(raw(p))
homes={'publicationTail':R/'artifacts/th14/publication-tail-nov06/stage3-prefix',
       'lowPause':R/'artifacts/th14/low-pause-input-key-native-nov09/input-key-prefix',
       'fullCampaign':R/'artifacts/th14/player-entry-end-menu-nov06/campaign'}
sources={};index={}
for name,home in homes.items():
 report=load(home/'report.json');assert report['childExited']and not report['error']
 profile=load(home/'untouched-first-player.json');data=raw(home/'selected-state.u32')
 assert len(data)==report['callbacks']*128 and hashlib.sha256(data).hexdigest()==report['selectedSha256']
 table=defaultdict(list)
 for callback,row in enumerate(struct.iter_unpack('<32I',data),1):table[row[30],row[0]].append((callback,row))
 index[name]=table
 sources[name]=dict(callbacks=report['callbacks'],replaySha256=report.get('sourceFullReplaySha256'),
                    actualInitialClock=profile['actualInitialTimeGetTimeInput'],securityCookie=profile['actualOriginalSecurityCookie'],
                    originalInstructionBytesPatched=report.get('instructionBytesPatched'),
                    firstScriptSeed=profile['words'][21],firstScriptCalls=profile['words'][22],
                    actualGameDiskFilesUnchanged=not report.get('originalDiskFilesChanged',False))
assert len({v['replaySha256']for v in sources.values()})==1
old=load(R/'artifacts/th14/shared-rate-closed-nov06/stage3-prefix-real/stage-pairs.json')
assert len(old['shotCountDifferences'])==3
cases=[]
for failure in old['shotCountDifferences']:
 key=(failure['stage'],failure['frame']);samples={}
 for name,table in index.items():
  matches=table.get(key,[])
  if len(matches)!=1:samples[name]=dict(unique=False,rows=len(matches));continue
  cb,row=matches[0];samples[name]=dict(unique=True,callback=cb,shotCount=row[26],scriptSeed=row[21],scriptCalls=row[22],visualSeed=row[23],visualCalls=row[24],playerX=row[3],playerY=row[4],power=row[15])
 cases.append(dict(originalFailure=failure,nativeSamples=samples))
full=load(R/'artifacts/th14/current-audio-full-normal-nov09/qualified.json')
result=dict(schema='thp/th14-retained-shot-input-audit/1',diagnosticOnly=True,sources=sources,cases=cases,
            sameReplayBytes=True,initialClockAndCookieDiffer=len({(s['actualInitialClock'],s['securityCookie'])for s in sources.values()})>1,
            nativeObserverBoundariesDiffer=True,doesNotProveIdenticalInputNondeterminism=True,
            originalCounterexamplesNotClosed=True,currentCppCorrectnessNotInferred=True,
            newGameOrReplayRuns=0,productionChanged=False,completeGame=False,bindings=bindings)
raw(Path(__file__));p=H/'retained-shot-inputs.json';assert not p.exists();p.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items()if k!='bindings'},indent=2))
