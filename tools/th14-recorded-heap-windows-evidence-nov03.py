"""Compare isolated x86 Windows heap runs against a finite original trace."""
from pathlib import Path
import argparse,hashlib,json,struct
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/replay-candidates-second-nov03/recorded-heap-windows-msvc';sha=lambda b:hashlib.sha256(b).hexdigest();plan_raw=(H/'process-end.json').read_bytes();plan=json.loads(plan_raw);raw=(R/'artifacts/th14/replay-candidates-second-nov03/combined-heap-original/main/native/crt-heap-events.jsonl').read_bytes();proof_raw=(R/'docs/porting/th14-combined-heap-trace-nov03.json').read_bytes();proof=json.loads(proof_raw);assert sha(raw)==plan['eventLogSha256']==proof['eventLogSha256'] and plan['actualWindowsProcessHeap'] and not plan['helperReceivesOriginalAddresses'] and plan['processes']==6 and plan['allocations']==838
assert sha((R/'tools/th14-recorded-heap-windows-helper-nov03.c').read_bytes())==plan['sourceSha256'] and sha((H/'helper.exe').read_bytes())==plan['executableSha256']
rows=[json.loads(x) for x in raw.splitlines()];alloc=[r for r in rows if r['event'] in ('crt-heap-allocation-return','zeroed-allocation-return')];assert len(alloc)==838
active={};actions=[];token=0
for row in rows:
 addr=row['address']
 if row['event'] in ('crt-heap-allocation-return','zeroed-allocation-return'):
  assert addr and addr not in active;active[addr]=token;actions.append((1,token,row['requestedBytes'],8 if row['event']=='zeroed-allocation-return' else 0));token+=1
 elif row['event']=='crt-free-entry':
  if not addr:continue
  assert addr in active;actions.append((2,active.pop(addr),0,0))
 else:raise AssertionError('unknown event')
header='#define HEAP_ALLOCATION_COUNT '+str(token)+'\n#define HEAP_ACTION_COUNT '+str(len(actions))+'\nstatic const struct Action heap_actions[HEAP_ACTION_COUNT]={\n'+''.join('{%d,%d,%d,%d},\n'%x for x in actions)+'};\n';assert (H/'heap-actions.h').read_text(encoding='ascii')==header and sha((H/'heap-actions.h').read_bytes())==plan['syntheticActionHeaderSha256']
runs=[]
for case in plan['cases']:
 data=(H/f"process-{case['index']}.bin").read_bytes();assert sha(data)==case['sha256'] and len(data)==case['bytes']==8+4*len(alloc) and struct.unpack_from('<2I',data)==(0x54485048,len(alloc));addresses=struct.unpack_from('<'+str(len(alloc))+'I',data,8);assert all(addresses)
 native_last={};helper_last={};all_matches=target_matches=target_relative=targets=0;first_original=first_helper=None
 for index,(row,address) in enumerate(zip(alloc,addresses)):
  previous=native_last.get(row['address']);helper_previous=helper_last.get(address);matched=previous==helper_previous;all_matches+=matched;native_last[row['address']]=index;helper_last[address]=index
  if row['event']=='crt-heap-allocation-return' and row['requestedBytes']==0x530c:
   targets+=1;target_matches+=matched
   if first_original is None:first_original=row['address'];first_helper=address
   target_relative+=row['address']-first_original==address-first_helper
 assert targets==32;runs.append(dict(index=case['index'],allAllocationReuseIdentityMatches=all_matches,targetSizeAllocations=targets,targetReuseIdentityMatches=target_matches,targetRelativePositionMatches=target_relative))
result=dict(verifiedFiniteWindowsHeapReplayExperiment=True,originalTraceCallbacks=proof['callbacks'],allocations=len(alloc),freeEntriesAssumedSuccessful=plan['freeEntriesAssumedSuccessful'],runs=runs,helperReceivesOnlySizesFlagsAndSyntheticLifetimes=True,actualOriginalAddressesProvidedToHelper=False,debugDeliveryOrderAssumedMemoryOrder=True,originalPriorProcessHeapStateReproduced=False,otherHeapPathsNotModeled=True,targetSizeIsNotProvenEnemy=True,actualWindowsProcessHeap=True,originalHeapHistoryReconstructed=False,rawPointersPublished=False,productionIntegrated=False,completeGame=False,nativeEquivalent=False,planSha256=sha(plan_raw),traceProofSha256=sha(proof_raw),eventLogSha256=sha(raw),toolSha256=sha(Path(__file__).read_bytes()),scope='Six isolated x86 processes execute the same sizes, flags and synthetic lifetime order on their own Windows process heap. Debug delivery order and free success are assumptions. Their process startup heap and all activity before the original observer attached are different or unknown; original addresses are compared only after the helpers exit.')
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');p.add_argument('--output',type=Path,default=R/'docs/porting/th14-recorded-heap-windows-nov03.json');a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'docs/porting') or out.is_relative_to(R/'artifacts/th14');data=(json.dumps(result,indent=2)+'\n').encode()
if a.check:assert out.read_bytes()==data
else:assert not out.exists();out.write_bytes(data)
print(json.dumps(result))
