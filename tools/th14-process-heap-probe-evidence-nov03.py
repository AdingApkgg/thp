"""Verify a standalone x86 Windows heap experiment without publishing pointers."""
from pathlib import Path
import argparse,hashlib,importlib,json,struct,sys
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/replay-candidates-second-nov03/process-heap-probe-msvc';sha=lambda b:hashlib.sha256(b).hexdigest();plan=json.loads((H/'process-end.json').read_bytes());source=R/'tools/th14-process-heap-probe-nov03.c';binary=H/'probe.exe';raw=binary.read_bytes();assert sha(raw)==plan['executableSha256'] and sha(source.read_bytes())==plan['sourceSha256'] and plan['architecture']=='x86' and plan['processes']==6 and not plan['originalGameLaunched'] and plan['actualWindowsProcessHeap']
pe=struct.unpack_from('<I',raw,0x3c)[0];assert raw[pe:pe+4]==b'PE\0\0' and struct.unpack_from('<H',raw,pe+4)[0]==0x14c;sys.path.insert(0,str(R/'tools'));Image=importlib.import_module('th12-pe').Image;image=Image(str(binary));directory=image.image_base+struct.unpack_from('<I',raw,pe+0x18+0x68)[0];imports=set()
for j in range(100):
 oft,_,_,name_rva,first=struct.unpack('<5I',image.read(directory+j*20,20))
 if not any([oft,name_rva,first]):break
 dll=image.cstring(image.image_base+name_rva);thunk=image.image_base+(oft or first)
 for k in range(100):
  value=image.u32(thunk+k*4)
  if not value:break
  assert not value&0x80000000;imports.add((dll.lower(),image.cstring(image.image_base+value+2)))
required=['GetProcessHeap','HeapAlloc','HeapFree','HeapSize','GetStdHandle','WriteFile','ExitProcess'];assert all(('kernel32.dll',name) in imports for name in required)
rows=[];heap_handles=[];first_allocations=[]
for case in plan['cases']:
 data=(H/f"process-{case['index']}.bin").read_bytes();assert len(data)==case['bytes']==120 and sha(data)==case['sha256'] and case['exitCode']==0;words=struct.unpack('<30I',data);assert words[0]==0x34485054 and words[1]!=0;initial=words[2:10];replacement=words[10:14];sizes=words[14:26];free_ok=words[26:30];assert len(set(initial))==8 and all(initial) and len(set(replacement))==4 and all(replacement) and all(x==0x530c for x in sizes) and all(x==1 for x in free_ok)
 heap_handles.append(words[1]);first_allocations.append(initial[0]);freed=[1,3,5,7];order=[next((i for i in freed if initial[i]==address),None) for address in replacement];stride=[initial[i+1]-initial[i] for i in range(7)];rows.append(dict(index=case['index'],allHeapSizeValuesEqualRequested=True,freeCallsSucceeded=4,reusedFreedBlocks=sum(x is not None for x in order),freedSlotReuseOrder=order,initialConsecutiveAddressDeltas=stride))
assert [r['index'] for r in rows]==list(range(6));result=dict(verifiedFiniteStandaloneProcessHeapExperiment=True,architecture='x86',processes=len(rows),requestedBytes=0x530c,cases=rows,distinctHeapHandles=len(set(heap_handles)),distinctFirstAllocationAddresses=len(set(first_allocations)),allCasesUseProcessHeapImport=True,allCasesReusedAllFourFreedBlocks=all(r['reusedFreedBlocks']==4 for r in rows),allCasesMatchSimpleFifo=all(r['freedSlotReuseOrder']==[1,3,5,7] for r in rows),allCasesMatchSimpleLifo=all(r['freedSlotReuseOrder']==[7,5,3,1] for r in rows),originalGameLaunched=False,originalGameHeapHistoryReproduced=False,windowsHeapAlgorithmOrStabilityProved=False,rawPointersPublished=False,nativeValuesProvidedToEngine=False,completeGame=False,nativeEquivalent=False,sourceSha256=plan['sourceSha256'],executableSha256=sha(raw),verifierSha256=sha(Path(__file__).read_bytes()),scope='Six independent x86 helper processes on this machine, each using its own GetProcessHeap. Eight allocations, four frees and four replacements of 0x530c bytes. Results depend on OS and prior helper heap state; they do not characterize the game process or guarantee general allocation order.')
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');p.add_argument('--output',type=Path,default=R/'docs/porting/th14-process-heap-probe-nov03.json');a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'docs/porting') or out.is_relative_to(H);data=(json.dumps(result,indent=2)+'\n').encode()
if a.check:assert out.read_bytes()==data
else:assert not out.exists();out.write_bytes(data)
print(json.dumps(result))
