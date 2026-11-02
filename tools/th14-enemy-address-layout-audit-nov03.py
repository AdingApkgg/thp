"""Compare selected enemy-state matches across two original runs of the same replay."""
from pathlib import Path
import argparse,collections,gzip,hashlib,json,struct
R=Path(__file__).resolve().parents[1];P=[R/'artifacts/th14/stage3-seed-store-live-v2-nov01/native',R/'artifacts/th14/reimu-controller-z-live-context-nov01/native'];sha=lambda b:hashlib.sha256(b).hexdigest();reports=[json.loads((p/'report.json').read_bytes()) for p in P];assert reports[0]['sourceFullReplaySha256']==reports[1]['sourceFullReplaySha256'] and reports[0]['callbacks']==26000 and reports[1]['callbacks']==36826 and all(r['childExited'] and not r['error'] for r in reports)
def capture(path):
 index_raw=(path/'combat-pool-index.json').read_bytes();index=json.loads(index_raw);layout=index['fields']['enemies'];assert len(layout)==31 and layout[0][0]=='instance';samples={}
 for entry in index['snapshots']:
  if entry['callback']>26000:continue
  raw=(path/'combat-pools'/entry['file']).read_bytes();assert sha(raw)==entry['sha256'];data=json.loads(gzip.decompress(raw));assert (data['callback'],data['stage'],data['stageFrame'])==(entry['callback'],entry['stage'],entry['stageFrame']) and entry['callback'] not in samples;rows=[]
  for row in data['original']['enemies']:
   blob=bytes.fromhex(row['rawHex']);rows.append((row['address'],tuple(struct.unpack_from('<I',blob,offset)[0] for _,offset in layout)))
  samples[entry['callback']]=((data['stage'],data['stageFrame']),rows)
 return samples,layout,sha(index_raw)
A,layoutA,indexA=capture(P[0]);B,layoutB,indexB=capture(P[1]);assert layoutA==layoutB;shared=sorted(set(A)&set(B));same=[callback for callback in shared if A[callback][0]==B[callback][0]];pairs=[]
for callback in same:
 left=collections.defaultdict(list);right=collections.defaultdict(list)
 for address,key in A[callback][1]:left[key].append(address)
 for address,key in B[callback][1]:right[key].append(address)
 for key in left.keys()&right.keys():
  if len(left[key])==len(right[key])==1:pairs.append((callback,key[0],left[key][0],right[key][0]))
pairs.sort();assert pairs;anchor=pairs[0][3]-pairs[0][2];matches=sum(b-a==anchor for _,_,a,b in pairs);deltas={b-a for _,_,a,b in pairs};assert len(deltas)>1 and matches<len(pairs)
result=dict(verifiedFiniteAddressLayoutComparison=True,sameSourceReplay=True,maxCallback=26000,sharedCallbackSamples=len(shared),sameStageAndFrameSamples=len(same),selectedEnemyFields=len(layoutA),uniqueSelectedFieldMatches=len(pairs),callbacksWithMatches=len({callback for callback,_,_,_ in pairs}),matchesUsingFirstObservedAddressDelta=matches,distinctAddressDeltas=len(deltas),singleBaseTranslationFitsAllMatchedSamples=False,identityMatchedOnlyBySelectedFieldsAndInstance=True,objectLifetimeIdentityAcrossProcessesProved=False,allocationHistoryOrCauseProved=False,rawAddressesOrSnapshotsPublished=False,nativeValuesProvidedToEngine=False,completeGame=False,nativeEquivalent=False,sourceReplaySha256=reports[0]['sourceFullReplaySha256'],nativeReportSha256=[sha((p/'report.json').read_bytes()) for p in P],combatIndexSha256=[indexA,indexB],verifierSha256=sha(Path(__file__).read_bytes()),scope='Two retained original processes using the same replay. At equal callback, stage and stage frame, match only unique identical 31-field enemy records including instance. Different address deltas rule out a universal base shift for these sampled matches, but do not establish cross-process object lifetime or allocator causality.')
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');p.add_argument('--output',type=Path,default=R/'docs/porting/th14-enemy-address-layout-audit-nov03.json');a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'docs/porting') or out.is_relative_to(R/'artifacts/th14');data=(json.dumps(result,indent=2)+'\n').encode()
if a.check:assert out.read_bytes()==data
else:assert not out.exists();out.write_bytes(data)
print(json.dumps(result))
