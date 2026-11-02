"""Independently bind one native shake-object stack observation and original instructions."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,struct
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/controller-delete-address-nov03';N=H/'native';bindings={};sha=lambda b:hashlib.sha256(b).hexdigest()
def raw(p):
 p=p.resolve();assert p.is_relative_to(R);v=p.read_bytes();bindings[p.relative_to(R).as_posix()]={'bytes':len(v),'sha256':sha(v)};return v
def load(p):return json.loads(raw(p))
summary=load(H/'verified.json');report=load(N/'report.json');end=load(H/'process-end.json');quiet=load(H/'native-silence-verified.json');pre=load(H/'observer-preflight.json');component=load(H/'original-destructor-component.json')
assert summary['passedFiniteObservation'] and summary['callbacks']==36823 and summary['originalControllerReads']==23 and summary['originalStackWrites']==13013
assert summary['ownedCallbackDeleteEntries']==1 and summary['readWordsMatchingObservedDeletedNode']==0 and summary['controllerReadsMatchingOuterShakeObjectThis']==1 and summary['originalSyntheticDestructorCases']==4
assert end['exitCode']==1 and end['guardStop'] is None and end['actualMastersZero'] and report['childExited'] and not report['error'] and report['controllerProbeDone'] and report['diagnosticPrefixOnly']
assert report['hardwareBreakpointsOnly'] and not report['instructionBytesPatched'] and not report['rngOrCounterWrites'] and report['gameStateWordWrites']==1 and report['caseInitialization']['attractBitClearOnly']
assert quiet['verifiedActualNativeMasterLevelsZero'] and quiet['nativePid']==report['pid'] and all(all(x[k]==0 for k in ['musicConfig','effectsConfig','musicMaster','effectsMaster']) for x in quiet['samples'])
observer=R/'tools/th14-controller-delete-address-observer-nov03.py';assert pre['processMutationCallsUnchanged'] and pre['newNodeReadsOnly'] and sha(raw(observer))==pre['observerSha256']==report['sourceSha256']==sha(raw(N/'observer-source.py'))
component_tool=R/'tools/th14-shake-retire-this-native-nov03.py';assert sha(raw(component_tool))==component['toolSha256'];spec=importlib.util.spec_from_file_location('shake_retire_native',component_tool);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);assert mod.observe()==component
for row in component['cases']:assert row['object']!=row['node'] and row['savedEsi']==row['object'] and row['freeArgs']==[row['node'],row['object']] and row['leaveReturnPc']=='0x46d4a7'
raw_events=raw(N/'controller-polar-z-stack-events.jsonl');raw_delete=raw(N/'controller-delete-entries.jsonl');assert sha(raw_events)==report['controllerProbeEventsSha256']==summary['controllerEventsSha256'] and sha(raw_delete)==report['controllerDeleteEntriesSha256']==summary['deleteEventsSha256']
events=[json.loads(x) for x in raw_events.splitlines()];deletes=[json.loads(x) for x in raw_delete.splitlines()];reads=[x for x in events if x['event']=='polar-z-before-read'];writes=[x for x in events if x['event']=='scratch-write-completed'];assert len(reads)==23 and len(writes)==13013 and len(deletes)==1
row=next(x for x in reads if x['precedingPlayerCallbacks']==36809);d=deletes[0];last=row['lastObservedWrite'];assert row['readOnly'] and last['readOnly'] and d['readOnly'] and not row['providedToEngine'] and not last['providedToEngine'] and not d['providedToEngine']
assert d['pc']==0x4016c0 and d['returnPc']==0x46d493 and d['originalInstructionBytes'].startswith('568bf156') and d['hostMonotonicNs']<last['hostMonotonicNs']<row['hostMonotonicNs']
st=bytes.fromhex(d['stackHex']);assert len(st)>=32;ret,node,node2,manager,obj,_,_,outer=struct.unpack_from('<8I',st);assert ret==0x46d493 and node==node2==d['nodeAddress'] and obj==row['word']==last['word']==last['registers']['esi'] and obj!=node and outer==0x46d18c
stack=bytes.fromhex(last['stackHex']);assert struct.unpack_from('<I',stack,20)[0]==0x46d4a7 and struct.pack('<I',0x4016de) in stack
mods=load(N/'controller-live-modules.json');dlls=[x for x in mods['rows'] if x['name'].lower()=='ntdll.dll' and x['base']<2**32];assert len(dlls)==1;dll=dlls[0];assert sha(Path(dll['path']).read_bytes())==component['ntdllSha256'] and last['pc']==dll['base']+333408+10
raw(H/'initial-node-only-verified.json');raw(H/'verify-capture.py')
result={'verifiedFiniteOriginalShakeObjectStackSource':True,'productionGameplayChanged':False,'originalCallbacks':36823,'controllerReads':23,'stackWrites':13013,'actualDeleteEntries':1,'controllerReadMatchedShakeObjectThis':1,'controllerReadMatchedDeletedCallbackNode':0,'originalInstructionComponentCases':4,'originalDllLeaveExecuted':True,'controlledAllocatorServices':True,'actualNativeMasterLevelsZero':True,'debuggerPausesAffectTiming':True,'nativeAddressesSuppliedToEngine':False,'portableHeapAddressModelImplemented':False,'strictPrefixAccepted':False,'completeGame':False,'nativeEquivalent':False,'bindings':bindings,'verifierSha256':sha(Path(__file__).read_bytes())}
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');p.add_argument('--output',type=Path,default=R/'docs/porting/th14-controller-shake-this-nov03.json');a=p.parse_args();target=a.output.resolve();assert target.is_relative_to(R/'docs/porting') or target.is_relative_to(H);data=(json.dumps(result,indent=2)+'\n').encode()
if a.check:assert target.read_bytes()==data
else:target.write_bytes(data)
print(json.dumps({k:v for k,v in result.items() if k!='bindings'}))
