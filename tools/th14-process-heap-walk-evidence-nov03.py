"""Audit x86 helper heap walks without exposing original pointers or claiming game equivalence."""
from pathlib import Path
import argparse,hashlib,importlib,json,struct,sys
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/replay-candidates-second-nov03/process-heap-walk-msvc-v3';sha=lambda b:hashlib.sha256(b).hexdigest();plan=json.loads((H/'process-end.json').read_bytes());source=R/'tools/th14-process-heap-walk-nov03.c';binary=H/'probe.exe';raw=binary.read_bytes();assert sha(raw)==plan['executableSha256'] and sha(source.read_bytes())==plan['sourceSha256'] and plan['architecture']=='x86' and plan['processes']==6 and not plan['originalGameLaunched'] and plan['actualWindowsProcessHeap']
pe=struct.unpack_from('<I',raw,0x3c)[0];assert raw[pe:pe+4]==b'PE\0\0' and struct.unpack_from('<H',raw,pe+4)[0]==0x14c;sys.path.insert(0,str(R/'tools'));Image=importlib.import_module('th12-pe').Image;image=Image(str(binary));directory=image.image_base+struct.unpack_from('<I',raw,pe+0x18+0x68)[0];imports=set()
for j in range(100):
 oft,_,_,name_rva,first=struct.unpack('<5I',image.read(directory+j*20,20))
 if not any([oft,name_rva,first]):break
 dll=image.cstring(image.image_base+name_rva);thunk=image.image_base+(oft or first)
 for k in range(100):
  value=image.u32(thunk+k*4)
  if not value:break
  assert not value&0x80000000;imports.add((dll.lower(),image.cstring(image.image_base+value+2)))
assert all(('kernel32.dll',name) in imports for name in ['GetProcessHeap','HeapAlloc','HeapFree','HeapLock','HeapUnlock','HeapWalk','GetLastError','GetStdHandle','WriteFile','ExitProcess'])
results=[]
for case in plan['cases']:
 data=(H/f"process-{case['index']}.bin").read_bytes();receipt=json.loads((H/f"process-{case['index']}-receipt.json").read_bytes());assert len(data)==case['bytes']==196676 and sha(data)==case['sha256'] and receipt==dict(index=case['index'],exitCode=0,bytes=196676,stderrBytes=0)
 header=struct.unpack_from('<17I',data);assert header[0]==0x57485054 and header[1]!=0;initial=header[2:10];replacement=header[10:14];counts=header[14:17];assert len(set(initial))==8 and len(set(replacement))==4 and all(0<count<4096 for count in counts)
 phases=[[struct.unpack_from('<4I',data,68+(phase*4096+k)*16) for k in range(counts[phase])] for phase in range(3)];first,free,final=phases;freed=[1,3,5,7];order=[next((i for i in freed if initial[i]==address),None) for address in replacement]
 def unique(rows,address,flags):
  found=[row for row in rows if row[0]==address and row[3]==flags];assert len(found)==1;return found[0]
 assert all(unique(first,address,4)[1:3]==(0x530c,12) for address in initial)
 assert all(unique(final,address,4)[1:3]==(0x530c,12) for address in initial)
 small=[unique(free,initial[i]+8,0) for i in freed[:3]];assert all(x[1:3]==(0x5308,16) for x in small)
 last=unique(free,initial[7]+8,0);tail=unique(first,initial[7]+0x5318+8,0);assert last[1]==0x530c+tail[1]+12 and last[2]==tail[2]==16
 results.append(dict(index=case['index'],heapEntryCounts=list(counts),replacementFreedSlots=order,initialAdjacentFreeBytes=tail[1],lastFreeBlockBytes=last[1],otherFreedBlockBytes=[x[1] for x in small],initialLastBlockAndAdjacentFreeListedSeparately=True,afterFreeSingleLargerFreeEntryObserved=True))
assert [x['index'] for x in results]==list(range(6));failed=json.loads((R/'artifacts/th14/replay-candidates-second-nov03/process-heap-walk-msvc-retry/process-0-receipt.json').read_bytes());assert failed['exitCode']==11 and failed['bytes']==0
result=dict(verifiedFiniteStandaloneHeapWalkExperiment=True,processes=len(results),requestedBytes=0x530c,heapEntryCapacity=4096,cases=results,allCasesSameFreedSlotOrder=all(x['replacementFreedSlots']==[5,3,1,7] for x in results),allCasesShowLargerLastFreeEntry=True,prior512EntryCapacityExceeded=True,priorFailedCaptureWasNotAccepted=True,heapWalkAndLockMayAffectTiming=True,originalGameLaunched=False,originalGameHeapHistoryReproduced=False,windowsHeapAlgorithmOrStabilityProved=False,rawPointersPublished=False,nativeValuesProvidedToEngine=False,completeGame=False,nativeEquivalent=False,sourceSha256=plan['sourceSha256'],executableSha256=sha(raw),verifierSha256=sha(Path(__file__).read_bytes()),scope='Six x86 helper processes with locked HeapWalk snapshots before frees, after frees and after replacement allocations. The last freed allocation and adjacent free entry are listed separately before the free and as one larger free entry afterward. This is consistent with coalescence in these helpers, but does not prove allocator internals or the game process heap history.')
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');p.add_argument('--output',type=Path,default=R/'docs/porting/th14-process-heap-walk-nov03.json');a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'docs/porting') or out.is_relative_to(H);encoded=(json.dumps(result,indent=2)+'\n').encode()
if a.check:assert out.read_bytes()==encoded
else:assert not out.exists();out.write_bytes(encoded)
print(json.dumps(result))
