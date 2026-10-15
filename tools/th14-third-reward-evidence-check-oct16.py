"""Recompute the stored third-counter correction evidence without rerunning producers."""
import hashlib,importlib.util,json,struct
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()

def main():
 doc=json.loads((ROOT/'docs/porting/th14-third-reward-observed-oct16.json').read_text())
 assert doc['schema']=='th14-third-reward-evidence-v1' and not doc['completeGame'] and not doc['nativeEquivalent']
 for name,row in doc['bindings'].items():
  path=(ROOT/name).resolve();assert path.is_relative_to(ROOT)
  data=path.read_bytes();assert len(data)==row['bytes'] and SHA(data)==row['sha256'],name
 assert SHA(Path(__file__).read_bytes())==doc['checkerSha256']
 base=ROOT/'artifacts/th14/third-reward-playbacks-oct16'
 build=json.loads((ROOT/'artifacts/th14/third-reward-core-build-oct16/build-result.json').read_text())
 assert build['productionSourceChanges']==['cpp/game/ShotTh14.cpp'] and build['engineObjects']==141
 for name,h in build['sourceHashes'].items():assert SHA((ROOT/'runtimes/th12/th12_web'/name).read_bytes())==h,name
 for row in build['outputs']:
  p=Path(row['path']);assert p.resolve().is_relative_to(ROOT);assert SHA(p.read_bytes())==row['sha256']
 native=json.loads((ROOT/'artifacts/th14/shot-third-reward-native-oct16.json').read_text())
 before=json.loads((ROOT/'artifacts/th14/shot-third-reward-check-oct16/before/receipt.json').read_text())
 after=json.loads((ROOT/'artifacts/th14/shot-third-reward-check-oct16/after/receipt.json').read_text())
 assert len(native['rows'])==1920 and before['differentCases']==960 and not after['differentCases']
 assert after['actualAllocationAttempts']==after['expectedAllocationAttempts']==8496 and after['oldImmutableRewardCasesPassed'] and after['oldImmutableRewardCases']==1440
 assert len(json.loads((ROOT/'artifacts/th14/shot-third-reward-check-oct16/before/all-differences.json').read_text()))==960
 assert json.loads((ROOT/'artifacts/th14/shot-third-reward-check-oct16/after/all-differences.json').read_text())==[]
 cases=[]
 for row in doc['playbacks']:
  key=row['key'];p=base/key;r=json.loads((p/'receipt.json').read_text());raw=(p/'selected-state.u32').read_bytes()
  assert r['callbacks']==row['callbacks'] and len(raw)==r['callbacks']*128 and SHA(raw)==r['selectedSha256']
  assert not r['error'] and not r['skipped'] and not r['unsupported'] and not r['forcedProgression'] and not r['invulnerabilityOverride']
  assert r['currentQueueFullPlaybackVerified']==row['naturalReplayEof'] and r['gameOverRequested']==row['gameOver']
  if key!='marisa-b':
   old=ROOT/'artifacts/th14'/('missing-shots-playbacks-oct16' if key in ('sakuya-b','marisa-a') else 'constructor-hit-playbacks-oct15')/key
   for name in ('selected-state.u32','callback-active.u8','enemy-owner.u8'):assert (p/name).read_bytes()==(old/name).read_bytes(),(key,name)
  cases.append(r)
 assert len(cases)==11 and sum(r['currentQueueFullPlaybackVerified'] for r in cases)==10
 assert sum(r['callbacks'] for r in cases)==880779
 spec=importlib.util.spec_from_file_location('fields',ROOT/'tools/th14-staged-loader-production-raw-evidence-check.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 prefix_rows=0
 for key,folder in [('sakuya-b','new-shot-native-prefixes-oct16'),('marisa-a','new-shot-native-serial-oct16'),('marisa-b','new-shot-native-serial-oct16')]:
  n=json.loads((ROOT/'artifacts/th14'/folder/key/'reference.json').read_text());raw=(base/key/'selected-state.u32').read_bytes();counts=Counter()
  for i,row in enumerate(n['frames']):
   assert row['index']==i
   for j,(a,b) in enumerate(zip(struct.unpack_from('<32I',raw,i*128),mod.normalize(row))):
    if a!=b:counts[mod.FIELDS[j]]+=1
  assert set(counts)<= {'visualSeed','visualCalls'},(key,dict(counts));prefix_rows+=len(n['frames'])
 assert prefix_rows==29088
 sanroot=ROOT/'artifacts/th14/third-reward-sanitized-oct16';san=json.loads((sanroot/'report.json').read_text())
 assert san['passed'] and san['nonrecoveringAddressAndUndefinedSanitizers'] and san['recompiledObjects']==1 and san['verifiedReusedObjects']==140
 assert san['sourceHashes']==build['sourceHashes'] and len(san['objectHashes'])==141
 for name,h in san['objectHashes'].items():assert SHA((sanroot/'objects'/(name.replace('/','_')+'.o')).read_bytes())==h
 for c in san['cases']:
  assert c['passed'] and not c['errors']
  for a,b in [('state.u32','selected-state.u32'),('active.u8','callback-active.u8'),('owners.u8','enemy-owner.u8')]:assert (sanroot/(c['key']+'.'+a)).read_bytes()==(base/c['key']/b).read_bytes()
 assert sum(c['callbacks'] for c in san['cases'])==326383
 detail=json.loads((base/'marisa-b/native-detail-comparison.json').read_text());assert detail['physicalRows']==211 and detail['words']==130725 and not detail['differences']
 sdl=json.loads((ROOT/'artifacts/th14/third-reward-sdl-build-oct16/build.json').read_text())
 for name,h in {**sdl['sourceHashes'],**sdl['headerHashes']}.items():assert SHA((ROOT/'runtimes/th12'/name).read_bytes())==h
 assert len(sdl['recompiledSources'])==146 and sdl['importsUnchanged'] and sdl['exportsUnchanged']
 assert sdl['wasmSha256']=='7e42a509065676ece981f2e8e5e7ce9a86d2960d02149398b1c0c0316c15f088'
 print(json.dumps(dict(storedEvidenceVerified=True,producerExecutedByChecker=False,nativeUnitCases=1920,oldRewardCases=1440,naturalReplayEofCases=10,totalCallbacks=880779,matchedNativePrefixCallbacks=prefix_rows,prefixSelectedGameplayDifferences=0,sanitizedCallbacks=326383,completeGame=False,nativeEquivalent=False)))
if __name__=='__main__':main()
