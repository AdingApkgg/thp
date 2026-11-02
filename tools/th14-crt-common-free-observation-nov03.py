"""Verify a bounded original boot CRT trace without inferring cross-thread order."""
from pathlib import Path
import argparse,collections,hashlib,json
R=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',type=Path,required=True);p.add_argument('--check',action='store_true');p.add_argument('--output',type=Path,required=True);a=p.parse_args();H=a.case.resolve();out=a.output.resolve();assert H.is_relative_to(R/'artifacts/th14') and (out.is_relative_to(H) or out.is_relative_to(R/'docs/porting'));N=H/'native';sha=lambda b:hashlib.sha256(b).hexdigest();native_raw=(N/'report.json').read_bytes();report=json.loads(native_raw);end=json.loads((H/'process-end.json').read_bytes());plan=json.loads((H/'plan.json').read_bytes());quiet=json.loads((H/'native-silence-verified.json').read_bytes());prepared=json.loads((H.parent.parent/'crt-common-free-observer-prepared.json').read_bytes())
assert end['guardStop'] is None and end['actualMastersZero'] and report['childExited'] and not report['error'] and report['callbacks']==plan['maximumCallbacks'] and report['diagnosticPrefixOnly'] and quiet['verifiedActualNativeMasterLevelsZero'] and quiet['nativePid']==report['pid'] and len(quiet['samples'])>=2
assert all(all(x[k]==0 for k in ['musicConfig','effectsConfig','musicMaster','effectsMaster']) for x in quiet['samples']) and report['executableSha256']=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
assert report['hardwareBreakpointsOnly'] and not report['instructionBytesPatched'] and not report['rngOrCounterWrites'] and not report['inputInjected'] and report['gameStateWordWrites']==1 and report['caseInitialization']['attractBitClearOnly'] and report['crtHeapObservationImplemented'] and plan['bootAndTrackedThreads'] and not plan['originalValuesProvidedToEngine']
observer=(N/'observer-source.py').read_bytes();assert sha(observer)==report['sourceSha256']==plan['sourceSha256']==prepared['generatedObserverSha256'];path=N/'crt-heap-events.jsonl';raw=path.read_bytes() if path.exists() else b'';assert (sha(raw) if raw else None)==report['crtHeapEventsSha256'];events=[json.loads(x) for x in raw.splitlines()];assert len(events)==report['crtHeapEvents']<=report['crtHeapEventLimit']==50000
active=collections.defaultdict(dict);sizes=collections.Counter();threads=set();allocations=frees=enemy=matched_enemy=matched_same_thread_free=unmatched_same_thread_free=duplicate_alloc=null_alloc=zero_callback=0;last_ns=last_callback=0
for row in events:
 assert row['readOnly'] and not row['nativeValuesProvidedToEngine'] and row['stage'] in (0,1) and 0<=row['precedingPlayerCallbacks']<=report['callbacks'] and row['hostMonotonicNs']>=last_ns and row['precedingPlayerCallbacks']>=last_callback;last_ns=row['hostMonotonicNs'];last_callback=row['precedingPlayerCallbacks'];tid=row['threadId'];threads.add(tid);address=row['address'];zero_callback+=int(row['precedingPlayerCallbacks']==0)
 if row['event']=='crt-heap-allocation-return':
  assert row['pc']==0x485589;size=row['requestedBytes'];sizes[size]+=1;allocations+=1
  if not address:null_alloc+=1;continue
  duplicate_alloc+=int(address in active[tid]);active[tid][address]=size
 elif row['event']=='crt-free-entry':
  assert row['pc']==0x4855d2;frees+=1
  if address in active[tid]:matched_same_thread_free+=1;del active[tid][address]
  else:unmatched_same_thread_free+=1
 elif row['event']=='enemy-allocation-return':
  assert row['pc']==0x421f08 and row['requestedBytes']==0x530c and address;enemy+=1;matched_enemy+=int(active[tid].get(address)==0x530c)
 else:raise AssertionError('unknown CRT heap event')
assert (allocations,frees,enemy)==(report['crtHeapAllocations'],report['crtHeapFrees'],report['crtHeapEnemyReturns'])
result=dict(verifiedFiniteOriginalBootCrtHeapTrace=True,callbacks=report['callbacks'],events=len(events),eventsWithZeroObservedPlayerCallbacks=zero_callback,threadsWithEvents=len(threads),crtAllocationReturns=allocations,crtFreeEntries=frees,enemyAllocationReturns=enemy,enemyReturnsMatchingSameThreadObservedCrtAllocation=matched_enemy,matchedSameThreadFreeEntries=matched_same_thread_free,unmatchedSameThreadFreeEntries=unmatched_same_thread_free,duplicateSameThreadAllocationsWithoutObservedFree=duplicate_alloc,nullAllocationReturns=null_alloc,commonRequestedSizes=[dict(bytes=k,count=v) for k,v in sizes.most_common(12)],debugExceptions=len(report['debugErrors']),actualMastersZero=True,trackedThreadsOnly=True,loaderBeforeAttachAndDirectOsCallsNotObserved=True,crossThreadDebugDeliveryOrderNotProvenMemoryOrder=True,freeEntryNotFreeSuccess=True,debuggerPausesAffectTiming=True,rawPointersPublished=False,nativeValuesProvidedToEngine=False,originalFullHeapHistoryProved=False,completeGame=False,nativeEquivalent=False,nativeReportSha256=sha(native_raw),eventLogSha256=sha(raw) if raw else None,observerSha256=sha(observer),verifierSha256=sha(Path(__file__).read_bytes()),scope='Finite original boot and first-stage CRT trace on threads tracked by the debugger. Zero callbacks means the observer had not yet recorded a Player callback. Matches are classified within the same thread only; loader activity before attach, direct OS heap calls, cross-thread actual order and free-call success remain unproved.')
data=(json.dumps(result,indent=2)+'\n').encode()
if a.check:assert out.read_bytes()==data
else:assert not out.exists();out.write_bytes(data)
print(json.dumps(result))
