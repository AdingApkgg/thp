"""Recover only directly saved stage-object context from the old worker snapshot."""
from pathlib import Path
import copy,hashlib,importlib,json,struct,sys
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/frame-rng-scope-nov02/retained-stack-context';H.mkdir(exist_ok=True);sys.path.insert(0,str(R/'tools'));sha=lambda b:hashlib.sha256(b).hexdigest()
image,*_=importlib.import_module('th-anm-handlers').handlers(14);assert sha(image.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
dis=Cs(CS_ARCH_X86,CS_MODE_32)
def instructions(addr,n):return [(i.address,i.mnemonic,i.op_str) for i in dis.disasm(image.read(addr,n),addr)]
a=instructions(0x40f250,0x60);assert (0x40f263,'mov','dword ptr [ebp - 8], edx') in a and (0x40f276,'mov','dword ptr [ebp - 0xc], eax') in a and (0x40f2a0,'mov','ecx, edi') in a and (0x40f2a2,'call','0x46fe50') in a
b=instructions(0x46fe50,0x4c);assert (0x46fe75,'mov','edi, ecx') in b and (0x46fe77,'mov','dword ptr [esp + 0x50], edi') in b and (0x46fe9a,'test','esi, esi') in b
assert (0x40da71,'call','0x40f250') in instructions(0x40da6f,7)
report_path=R/'artifacts/th14/reimu-controller-z-live-context-nov01/native/report.json';report=json.loads(report_path.read_bytes());rows=[e for e in report['transitionEvents'] if e['event']=='replay-seeds-restored-before-globals-copy' and e['stage']==3];assert len(rows)==1
def decode(e):
 assert e['pc']==0x456133 and e['precedingPlayerCallbacks']==22335 and e['stageFrame']==0
 m=e['mainThreadContextAtWorkerEvent'];r=m['registers'];assert r['eip']==0x46fe9a and m['readOnly'] and m['diagnosticOnly'] and not m['providedToEngine']
 data=bytes.fromhex(m['stackHex']);base=r['esp'];assert len(data)==m['stackBytes']==512
 def u32(p):
  off=p-base;assert 0<=off<=len(data)-4;return struct.unpack_from('<I',data,off)[0]
 vmframe=r['ebp'];objectframe=u32(vmframe);assert u32(vmframe+4)==0x40f2a7 and u32(objectframe+4)==0x40da76
 descriptor,index,owner=(u32(objectframe-12),u32(objectframe-8),u32(objectframe-4));vm=u32((vmframe&~7)-0xf0);primitive=u32((vmframe&~7)-0x13c)
 assert index==6 and vm==r['edi']==r['ecx'] and all(0x10000<=v<0x7fff0000 for v in [descriptor,owner,vm,primitive])
 return {'precedingPlayerCallbacks':e['precedingPlayerCallbacks'],'workerPc':hex(e['pc']),'mainPc':hex(r['eip']),'objectIndex':index,'ownerAddress':hex(owner),'descriptorAddress':hex(descriptor),'vmAddress':hex(vm),'primitiveAddress':hex(primitive),'vmFrameReturn':hex(u32(vmframe+4)),'objectFrameReturn':hex(u32(objectframe+4))}
found=decode(rows[0]);controls=[]
for kind in ['wrong-main-pc','wrong-vm-return','wrong-object-index','wrong-saved-this']:
 e=copy.deepcopy(rows[0]);m=e['mainThreadContextAtWorkerEvent'];r=m['registers'];data=bytearray.fromhex(m['stackHex']);base=r['esp'];vmframe=r['ebp'];obj=struct.unpack_from('<I',data,vmframe-base)[0]
 if kind=='wrong-main-pc':r['eip']+=1
 elif kind=='wrong-vm-return':struct.pack_into('<I',data,vmframe+4-base,0x40f2a8)
 elif kind=='wrong-object-index':struct.pack_into('<I',data,obj-8-base,7)
 else:struct.pack_into('<I',data,(vmframe&~7)-0xf0-base,0)
 m['stackHex']=data.hex()
 try:decode(e)
 except AssertionError:controls.append({'name':kind,'rejected':True})
 else:raise AssertionError('bad context accepted '+kind)
result={'passed':True,'originalExecutableSha256':sha(image.data),'retainedReportSha256':sha(report_path.read_bytes()),'result':found,'tamperControls':controls,'interpretation':'The saved index and this pointer agree with the original object-loop and ANM call instructions. No VM bytes, owner table, primitive bytes, file or script were captured at this old event; individual VM identity and exact worker-versus-main instruction ordering remain unproved.','newOriginalProcessLaunched':False,'snapshotValuesProvidedToEngine':False,'productionChanged':False,'completeGame':False,'nativeEquivalent':False,'toolSha256':sha(Path(__file__).read_bytes())}
(H/'verified.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['interpretation']}))
