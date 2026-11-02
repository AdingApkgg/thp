"""Classify the finite trace's address reuse in debugger delivery order only."""
from pathlib import Path
import argparse, collections, hashlib, json

R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/replay-candidates-second-nov03/crt-common-free-original/main'
sha=lambda b:hashlib.sha256(b).hexdigest()

def classify(rows):
    active={};last={};free_events=collections.defaultdict(list);counts=collections.Counter()
    for i,row in enumerate(rows):
        typ=row['event'];address=row['address'];tid=row['threadId']
        if typ=='crt-free-entry':
            if not address: counts['nullFreeEntries']+=1;continue
            free_events[address].append((i,tid))
            previous=active.pop(address,None)
            if previous is None: counts['unmatchedNonNullFreeEntries']+=1
            else:
                counts['matchedFreeEntries']+=1
                if previous[0]!=tid:counts['crossThreadMatchedFreeEntries']+=1
        elif typ=='crt-heap-allocation-return':
            if not address: counts['nullAllocationReturns']+=1;continue
            key=(tid,address)
            if key in last:
                between=[other for index,other in free_events[address] if last[key]<index<i]
                if tid not in between:
                    counts['sameThreadDuplicateWithoutSameThreadFree']+=1
                    if between: counts['duplicatesWithOtherThreadFreeBetween']+=1
                    else: counts['duplicatesWithNoObservedFreeBetween']+=1
            if address in active: counts['duplicateWhileGloballyActive']+=1
            active[address]=(tid,i);last[key]=i;counts['nonNullAllocationReturns']+=1
        else: assert typ=='enemy-allocation-return'
    counts['activeAtEndInRecordedOrder']=len(active)
    return counts

# Distinguish a cross-thread entry, an absent entry, and a same-thread entry.
def alloc(t,a): return dict(event='crt-heap-allocation-return',threadId=t,address=a)
def free(t,a): return dict(event='crt-free-entry',threadId=t,address=a)
control=classify([alloc(1,1),free(2,1),alloc(1,1),alloc(3,2),alloc(3,2),alloc(4,3),free(4,3),alloc(4,3),free(5,0)])
assert control['sameThreadDuplicateWithoutSameThreadFree']==2 and control['duplicatesWithOtherThreadFreeBetween']==1 and control['duplicatesWithNoObservedFreeBetween']==1 and control['duplicateWhileGloballyActive']==1 and control['nullFreeEntries']==1
proof_raw=(R/'docs/porting/th14-crt-common-free-trace-nov03.json').read_bytes();proof=json.loads(proof_raw)
raw=(H/'native/crt-heap-events.jsonl').read_bytes();assert sha(raw)==proof['eventLogSha256'] and proof['verifiedFiniteOriginalBootCrtHeapTrace'] and proof['debugExceptions']==0
rows=[json.loads(line) for line in raw.splitlines()];counts=classify(rows)
assert counts['sameThreadDuplicateWithoutSameThreadFree']==proof['duplicateSameThreadAllocationsWithoutObservedFree']
assert counts['nonNullAllocationReturns']+counts['nullAllocationReturns']==proof['crtAllocationReturns']
assert counts['matchedFreeEntries']+counts['unmatchedNonNullFreeEntries']+counts['nullFreeEntries']==proof['crtFreeEntries']
result=dict(verifiedRecordedDebugDeliveryOrderClassification=True,callbacks=proof['callbacks'],events=len(rows),counts=dict(sorted(counts.items())),syntheticPositiveAndNegativeControlsPassed=True,actualMemoryOrderProved=False,freeSuccessProved=False,loaderBeforeAttachAndDirectOsCallsObserved=False,originalFullHeapHistoryProved=False,nativeValuesProvidedToEngine=False,rawPointersPublished=False,productionIntegrated=False,completeGame=False,nativeEquivalent=False,proofSha256=sha(proof_raw),eventLogSha256=sha(raw),toolSha256=sha(Path(__file__).read_bytes()),scope='Address identities are classified in the debugger event delivery order only. A free entry is not a successful free, and cross-thread delivery order is not proved to match actual memory operations. The loader before attach and direct OS calls are unobserved.')
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');p.add_argument('--output',type=Path,default=R/'docs/porting/th14-crt-cross-thread-order-nov03.json');a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'docs/porting') or out.is_relative_to(R/'artifacts/th14');data=(json.dumps(result,indent=2)+'\n').encode()
if a.check:assert out.read_bytes()==data
else:assert not out.exists();out.write_bytes(data)
print(json.dumps(result))
