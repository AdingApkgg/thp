"""Verify finite original primary/zeroed allocations and common-free trace."""
from pathlib import Path
import argparse,collections,hashlib,json
R=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args();H=a.case.resolve();out=a.output.resolve();assert H.is_relative_to(R/'artifacts/th14') and (out.is_relative_to(H) or out.is_relative_to(R/'docs/porting'));N=H/'native';sha=lambda b:hashlib.sha256(b).hexdigest();native=(N/'report.json').read_bytes();report=json.loads(native);end=json.loads((H/'process-end.json').read_bytes());plan=json.loads((H/'plan.json').read_bytes());quiet=json.loads((H/'native-silence-verified.json').read_bytes());prepared=json.loads((H.parent.parent/'combined-heap-observer-prepared.json').read_bytes())
assert end['guardStop'] is None and end['actualMastersZero'] and report['childExited'] and not report['error'] and report['callbacks']==plan['maximumCallbacks'] and report['diagnosticPrefixOnly'] and quiet['verifiedActualNativeMasterLevelsZero'] and quiet['nativePid']==report['pid'] and len(quiet['samples'])>=2
assert all(all(x[k]==0 for k in ['musicConfig','effectsConfig','musicMaster','effectsMaster']) for x in quiet['samples']) and report['executableSha256']=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
assert report['hardwareBreakpointsOnly'] and not report['instructionBytesPatched'] and not report['rngOrCounterWrites'] and not report['inputInjected'] and report['gameStateWordWrites']==1 and report['caseInitialization']['attractBitClearOnly'] and report['crtHeapObservationImplemented'] and plan['bootAndTrackedThreads'] and not plan['originalValuesProvidedToEngine']
observer=(N/'observer-source.py').read_bytes();assert sha(observer)==report['sourceSha256']==plan['sourceSha256']==prepared['generatedObserverSha256'];raw=(N/'crt-heap-events.jsonl').read_bytes();assert sha(raw)==report['crtHeapEventsSha256'];rows=[json.loads(x) for x in raw.splitlines()];assert len(rows)==report['crtHeapEvents']<=report['crtHeapEventLimit']==50000
active={};counts=collections.Counter();threads=set();sizes=collections.Counter();last_ns=last_callback=0
for row in rows:
 assert row['readOnly'] and not row['nativeValuesProvidedToEngine'] and row['stage'] in (0,1) and 0<=row['precedingPlayerCallbacks']<=report['callbacks'] and row['hostMonotonicNs']>=last_ns and row['precedingPlayerCallbacks']>=last_callback
 last_ns=row['hostMonotonicNs'];last_callback=row['precedingPlayerCallbacks'];threads.add(row['threadId']);address=row['address'];counts['eventsBeforeFirstObservedPlayerCallback']+=row['precedingPlayerCallbacks']==0
 if row['event'] in ('crt-heap-allocation-return','zeroed-allocation-return'):
  assert row['pc']==(0x485589 if row['event']=='crt-heap-allocation-return' else 0x494fc1) and row['requestedBytes']>=0
  if row['event']=='zeroed-allocation-return':assert row['heapFlags']==8
  counts[row['event']]+=1;sizes[row['requestedBytes']]+=1
  if not address:counts['nullAllocationReturns']+=1;continue
  if address in active:counts['duplicateActiveInRecordedOrder']+=1
  active[address]=(row['threadId'],row['event'],row['requestedBytes'])
  if row['event']=='crt-heap-allocation-return' and row['requestedBytes']==0x530c:counts['primaryAllocationsWithEnemyObjectSize']+=1
 elif row['event']=='crt-free-entry':
  assert row['pc']==0x4855d2;counts['freeEntries']+=1
  if not address:counts['nullFreeEntries']+=1;continue
  previous=active.pop(address,None)
  if previous is None:counts['unmatchedNonNullFreeEntries']+=1
  else:
   counts['matchedFreeEntriesInRecordedOrder']+=1
   if previous[0]!=row['threadId']:counts['crossThreadMatchedFreeEntries']+=1
 else:raise AssertionError('unknown event')
assert counts['crt-heap-allocation-return']==report['crtHeapAllocations'] and counts['zeroed-allocation-return']==report['crtHeapZeroedReturns'] and counts['freeEntries']==report['crtHeapFrees']
result=dict(verifiedFiniteOriginalCombinedHeapTrace=True,callbacks=report['callbacks'],events=len(rows),counts=dict(sorted(counts.items())),threadsWithEvents=len(threads),activeAtEndInRecordedOrder=len(active),commonRequestedSizes=[dict(bytes=k,count=v) for k,v in sizes.most_common(12)],debugExceptions=len(report['debugErrors']),actualMastersZero=True,enemyFactoryNotObserved=True,enemySizedAllocationsNotProvenEnemyObjects=True,trackedThreadsOnly=True,loaderBeforeAttachAndOtherHeapPathsNotObserved=True,crossThreadDebugDeliveryOrderNotProvenMemoryOrder=True,freeEntryNotFreeSuccess=True,debuggerPausesAffectTiming=True,rawPointersPublished=False,nativeValuesProvidedToEngine=False,originalFullHeapHistoryProved=False,completeGame=False,nativeEquivalent=False,nativeReportSha256=sha(native),eventLogSha256=sha(raw),observerSha256=sha(observer),verifierSha256=sha(Path(__file__).read_bytes()),scope='Finite trace of primary and zeroed allocation returns and common CRT free entry on debugger-tracked threads. Pairing uses debug delivery order, not a proved cross-thread memory order; release success, earlier activity, and other heap paths are not established. Allocation size alone does not prove an enemy object.')
data=(json.dumps(result,indent=2)+'\n').encode()
if a.check:assert out.read_bytes()==data
else:assert not out.exists();out.write_bytes(data)
print(json.dumps(result))
