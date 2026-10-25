"""Execute original geometry on retained VMs; never mutate the live process."""
from pathlib import Path
import argparse,hashlib,importlib,json,struct,sys
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--inventory',type=Path,default=ROOT/'docs/porting/th14-mode-acceptance-inventory-oct25.json')
args=parser.parse_args();OUT=args.output.resolve()
assert OUT.is_relative_to(ROOT/'artifacts/th14');OUT.mkdir(exist_ok=False)
sys.path.insert(0,str(ROOT/'tools'))
Image=importlib.import_module('th12-pe').Image
target=json.loads((ROOT/'runtimes/th14/target.json').read_bytes())
image=Image(str((ROOT/'runtimes/th14'/target['executable']).resolve()))
SHA=lambda b:hashlib.sha256(b).hexdigest()
assert SHA(image.data)==target['sha256']=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
inventory_raw=args.inventory.read_bytes();inventory=json.loads(inventory_raw)
BASE,STACK,RETURN,OUTPUT=0x70000000,0x700ff000,0x700fe000,0x70010000
bindings={args.inventory.resolve().relative_to(ROOT).as_posix():SHA(inventory_raw)};observations=[];root_count=child_count=parent_x_changed=0
def read(path):
 raw=path.read_bytes();bindings[path.relative_to(ROOT).as_posix()]=SHA(raw);return raw
for key in ['reimua-easy','reimua-normal']:
 case=next(row for row in inventory['cases']if row['key']==key)
 capture=case['retainedNaturalRuns'][0]
 comparison=ROOT/capture['selected32ComparisonReports'][0]['path']
 live=json.loads(read(comparison.parent/'live-report.json'))
 for snap in live['snapshots']:
  differences=[row for row in snap['differences']if row.get('field')=='worldZ']
  if not differences:continue
  native=json.loads(read(ROOT/capture['path']/f'live-vms-callback-{snap["frame"]}.json'))
  blobs={row['handle']:bytes.fromhex(row['rawVmHex'])for row in native['rows']}
  word=lambda b,o:struct.unpack_from('<I',b,o)[0]
  addresses={handle:word(blob,0x570)for handle,blob in blobs.items()}
  by_address={addresses[handle]:blob for handle,blob in blobs.items()}
  m=Uc(UC_ARCH_X86,UC_MODE_32);mapped=set()
  def map_region(address,count):
   for page in range(address&~4095,(address+count+4095)&~4095,4096):
    if page not in mapped:m.mem_map(page,4096);mapped.add(page)
  for _,address,size,raw,count in image.sections:
   map_region(address,size);m.mem_write(address,image.data[raw:raw+count])
  map_region(BASE,0x100000)
  for address,blob in by_address.items():map_region(address,len(blob));m.mem_write(address,blob)
  # Explicit 640x480 diagnostic render-space globals, identical in each pair.
  m.mem_write(0x4f7a6c,struct.pack('<f',1));m.mem_write(0x4f7a80,struct.pack('<4I',320,16,320,16))
  pcs=[]
  m.hook_add(UC_HOOK_CODE,lambda machine,address,size,data:pcs.append(address))
  def run(entry,args):
   pcs.clear();m.mem_write(STACK,struct.pack('<'+'I'*(len(args)+1),RETURN,*args))
   m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,0)
   m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
   m.reg_write(UC_X86_REG_MXCSR,0x1f80)
   m.emu_start(entry,RETURN,count=100000)
   assert m.reg_read(UC_X86_REG_EIP)==RETURN,hex(m.reg_read(UC_X86_REG_EIP))
   return m.reg_read(UC_X86_REG_EAX),list(pcs)
  def vertices(address):
   m.mem_write(OUTPUT,b'\xcd'*48)
   run(0x4766e0,[address,*[OUTPUT+12*i for i in range(4)]])
   return bytes(m.mem_read(OUTPUT,48))
  for diff in differences:
   blob=blobs[diff['handle']];address=addresses[diff['handle']]
   assert word(blob,0x18)&3==2 and word(blob,0x5bc)==0
   status,trace=run(0x478f60,[address])
   assert status==0xffffffff and trace[-1]==0x478f8d
   assert all(0x478f60<=pc<=0x478f8d for pc in trace)
   root_count+=1
   descendants=[];frontier=[address];seen={address}
   while frontier:
    parent=frontier.pop()
    for candidate,child in by_address.items():
     if word(child,0x594)==parent:
      assert candidate not in seen;seen.add(candidate);descendants.append(candidate);frontier.append(candidate)
   for child_address in descendants:
    child=by_address[child_address];assert (word(child,0x18)>>25)&31==1
    baseline=vertices(child_address)
    m.mem_write(address+0x5a4,b'\0'*4);cleared=vertices(child_address)
    assert baseline==cleared,'Parent Z affects native vertices'
    m.mem_write(address,blob)
    child_x=struct.unpack_from('<f',child,0x59c)[0]
    m.mem_write(child_address+0x59c,struct.pack('<f',child_x+32))
    assert vertices(child_address)!=baseline,'Own-X positive control did not alter geometry'
    m.mem_write(child_address,child)
    parent_x=struct.unpack_from('<f',blob,0x59c)[0]
    m.mem_write(address+0x59c,struct.pack('<f',parent_x+32))
    affects_parent=vertices(child_address)!=baseline;parent_x_changed+=int(affects_parent)
    m.mem_write(address,blob);assert vertices(child_address)==baseline
    observations.append(dict(case=key,callback=snap['frame'],descendantDepth='live recursive parent relation',parentZClearedVerticesEqual=True,ownXPositiveControlChanged=True,parentXPositiveControlChanged=affects_parent,baselineVerticesSha256=SHA(baseline)))
    child_count+=1
assert root_count==33 and child_count==39 and parent_x_changed>0
result=dict(verifiedOriginalInstructionComponent=True,nativeProcessOrGpuRun=False,originalExecutableSha256=target['sha256'],hiddenRootCount=root_count,hiddenRootsAllSkippedBeforeMaterialAndGeometry=True,descendantGeometryCases=child_count,vertexOutputBytesPerCase=48,allParentZInterventionsByteIdentical=True,allOwnXPositiveControlsChanged=True,parentXPositiveControlsChanged=parent_x_changed,observations=observations,bindings=bindings,toolSha256=SHA(Path(__file__).read_bytes()),liveOriginalOrProductionStateWritten=False,scope='Original478f60/4766e0 instruction execution under Unicorn on retained snapshots and an explicit640x480 context. Proves only the observed hidden roots and present descendants at these boundaries; not later lifecycle, complete game images or arbitrary inputs.',rawZDifferencesStillRetained=True,completeGame=False,nativeEquivalent=False)
(OUT/'report.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({key:result[key]for key in ['hiddenRootCount','descendantGeometryCases','allParentZInterventionsByteIdentical','parentXPositiveControlsChanged']}))
