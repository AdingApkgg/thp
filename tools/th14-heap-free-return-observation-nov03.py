"""Verify per-thread CRT free entries and actual HeapFree return statuses."""
from pathlib import Path
import argparse,collections,hashlib,json
R=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args();H=a.case.resolve();out=a.output.resolve();assert H.is_relative_to(R/'artifacts/th14') and (out.is_relative_to(H) or out.is_relative_to(R/'docs/porting'));N=H/'native';sha=lambda b:hashlib.sha256(b).hexdigest();native=(N/'report.json').read_bytes();report=json.loads(native);end=json.loads((H/'process-end.json').read_bytes());plan=json.loads((H/'plan.json').read_bytes());quiet=json.loads((H/'native-silence-verified.json').read_bytes());prepared=json.loads((H.parent.parent/'heap-free-return-observer-prepared.json').read_bytes())
assert end['guardStop'] is None and end['actualMastersZero'] and report['childExited'] and not report['error'] and report['callbacks']==plan['maximumCallbacks'] and report['diagnosticPrefixOnly'] and quiet['verifiedActualNativeMasterLevelsZero'] and quiet['nativePid']==report['pid'] and len(quiet['samples'])>=2
assert all(all(x[k]==0 for k in ['musicConfig','effectsConfig','musicMaster','effectsMaster']) for x in quiet['samples']) and report['executableSha256']=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
assert report['hardwareBreakpointsOnly'] and not report['instructionBytesPatched'] and not report['rngOrCounterWrites'] and not report['inputInjected'] and report['gameStateWordWrites']==1 and report['caseInitialization']['attractBitClearOnly'] and report['crtHeapObservationImplemented'] and plan['bootAndTrackedThreads'] and not plan['originalValuesProvidedToEngine']
observer=(N/'observer-source.py').read_bytes();assert sha(observer)==report['sourceSha256']==plan['sourceSha256']==prepared['generatedObserverSha256'];raw=(N/'crt-heap-events.jsonl').read_bytes();assert sha(raw)==report['crtHeapEventsSha256'];rows=[json.loads(x) for x in raw.splitlines()];assert len(rows)==report['crtHeapEvents']<=report['crtHeapEventLimit']==50000
pending={};active={};counts=collections.Counter();threads=set();last_ns=last_callback=0
for row in rows:
 assert row['readOnly'] and not row['nativeValuesProvidedToEngine'] and row['stage'] in (0,1) and 0<=row['precedingPlayerCallbacks']<=report['callbacks'] and row['hostMonotonicNs']>=last_ns and row['precedingPlayerCallbacks']>=last_callback
 last_ns=row['hostMonotonicNs'];last_callback=row['precedingPlayerCallbacks'];tid=row['threadId'];threads.add(tid);address=row['address'];counts['eventsBeforeFirstObservedPlayerCallback']+=row['precedingPlayerCallbacks']==0
 if row['event'] in ('crt-heap-allocation-return','zeroed-allocation-return'):
  assert row['pc']==(0x485589 if row['event']=='crt-heap-allocation-return' else 0x494fc1) and row['requestedBytes']>=0
  if row['event']=='zeroed-allocation-return':assert row['heapFlags']==8
  counts[row['event']]+=1
  if not address:counts['nullAllocationReturns']+=1;continue
  if address in active:counts['allocationWhileActiveInReturnDeliveryOrder']+=1
  active[address]=tid
  if row['event']=='crt-heap-allocation-return' and row['requestedBytes']==0x530c:counts['primaryAllocationsWithEnemyObjectSize']+=1
 elif row['event']=='crt-free-entry':
  assert row['pc']==0x4855d2;counts['freeEntries']+=1
  if not address:counts['nullFreeEntries']+=1;continue
  assert tid not in pending;pending[tid]=address
 elif row['event']=='crt-free-return':
  assert row['pc']==0x4855ec and isinstance(row['success'],bool) and pending.pop(tid)==address;counts['freeReturns']+=1
  if not row['success']:counts['failedFreeReturns']+=1;continue
  counts['successfulFreeReturns']+=1;previous=active.pop(address,None)
  if previous is None:counts['successfulFreeUnmatchedInReturnDeliveryOrder']+=1
  else:
   counts['successfulFreeMatchedInReturnDeliveryOrder']+=1
   if previous!=tid:counts['crossThreadSuccessfulFreeMatches']+=1
 else:raise AssertionError('unknown event')
assert counts['crt-heap-allocation-return']==report['crtHeapAllocations'] and counts['zeroed-allocation-return']==report['crtHeapZeroedReturns'] and counts['freeEntries']==report['crtHeapFrees'] and counts['freeReturns']==report['crtHeapFreeReturns'] and len(pending)==report['crtHeapPendingFreeReturns']
result=dict(verifiedFiniteOriginalHeapFreeReturnTrace=True,callbacks=report['callbacks'],events=len(rows),counts=dict(sorted(counts.items())),threadsWithEvents=len(threads),pendingNonNullFreeReturns=len(pending),activeAtEndInReturnDeliveryOrder=len(active),debugExceptions=len(report['debugErrors']),actualMastersZero=True,freeSuccessObservedAtOperatingSystemReturn=True,enemyFactoryNotObserved=True,enemySizedAllocationsNotProvenEnemyObjects=True,trackedThreadsOnly=True,loaderBeforeAttachAndOtherHeapPathsNotObserved=True,crossThreadDebugDeliveryOrderNotProvenMemoryOrder=True,debuggerPausesAffectTiming=True,rawPointersPublished=False,nativeValuesProvidedToEngine=False,originalFullHeapHistoryProved=False,completeGame=False,nativeEquivalent=False,nativeReportSha256=sha(native),eventLogSha256=sha(raw),observerSha256=sha(observer),verifierSha256=sha(Path(__file__).read_bytes()),scope='Finite trace on debugger-tracked threads, with per-thread breakpoint rotation from non-null CRT free entry to the actual imported HeapFree return. Return statuses are observed; actual cross-thread heap-operation order, untracked paths, and pre-attach history remain unproved. Allocation size does not establish enemy identity.')
data=(json.dumps(result,indent=2)+'\n').encode()
if a.check:assert out.read_bytes()==data
else:assert not out.exists();out.write_bytes(data)
print(json.dumps(result))
