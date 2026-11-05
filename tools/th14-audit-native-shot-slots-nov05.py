"""Compare actual original slot/VM snapshots to the independent portable run.

Raw differences stay private. Missing parents/unsupported geometry are counted,
never converted to passes. This covers selected fields, not complete VM memory.
"""
from collections import Counter
from pathlib import Path
import gzip,hashlib,importlib,json,struct,sys
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import UC_X86_REG_ECX,UC_X86_REG_EIP,UC_X86_REG_ESP,UC_X86_REG_MXCSR,UC_X86_REG_FPCW,UC_X86_REG_FPSW,UC_X86_REG_FPTAG

R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/shot-lifetime-native-nov05'
SHA=lambda data:hashlib.sha256(data).hexdigest();bindings={}


def raw(path):
    data=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(data),sha256=SHA(data));return data


def read(path):return json.loads(raw(path))


native=H/'prefix-slots-v2/native';portable=H/'comparison-on/model'
result=read(H/'comparison-on/result.json')
assert result['strictDriverExitCode']==0 and result['rawVerifierExitCode']==0
ni=read(native/'shot-lifetime-index.json');pi=read(portable/'shot-lifetime-index.json')
nmap={x['callback']:x for x in ni['snapshots']}
assert len(nmap)==len(ni['snapshots'])
sys.path.insert(0,str(R/'tools'));image=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
assert SHA(image.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
m=Uc(UC_ARCH_X86,UC_MODE_32)
for _,base,size,offset,n in image.sections:
    first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,image.data[offset:offset+n])
BASE,VM,OUTPUT,STACK,RETURN=0x70000000,0x70001000,0x70003000,0x700ff000,0x700fe000
m.mem_map(BASE,0x100000);m.mem_write(0x4854a0,b'\xc3')
put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
word=lambda blob,offset:struct.unpack_from('<I',blob,offset)[0]
shot_fields={1:0x98,2:0x14,4:0x18,5:0x1c,6:0x20,7:0x10,9:0xac,10:0xa8,11:0xa4,
    12:0x54,13:0x58,14:0x5c,15:0x88,16:0x8c,17:0x6c,18:0x70}
vm_fields={31:0x4a0,32:0x548,33:0x54c,34:0x550,35:0x560,40:0x59c,41:0x5a0,42:0x5a4,
    43:0x3c,44:0x40,45:0x44,46:0x4ec,47:0x4f0,48:0x4f4,49:0x50,
    50:0x60,51:0x64,52:0x68,53:0x6c,54:0x80,55:0x84,56:0x90,57:0x94,
    **{80+i:0x4ac+i*4 for i in range(8)}}
differences=[];counts=Counter();compared=Counter();quads=0;missing=Counter();availability=Counter();summary=[]


def check(kind,index,a,b,callback,slot):
    compared[kind]+=1
    if a!=b:
        counts[kind]+=1;differences.append(dict(callback=callback,slot=slot,kind=kind,field=index,native=a,portable=b))


for item in pi['snapshots']:
    callback=item['callback'];nitem=nmap[callback]
    assert (item['stage'],item['stageFrame'])==(nitem['stage'],nitem['stageFrame'])
    blob=raw(native/'shot-lifetime'/nitem['file']);assert SHA(blob)==nitem['sha256']
    n= json.loads(gzip.decompress(blob));pool=bytes.fromhex(n['shotPoolRawHex'])
    assert len(pool)==256*0xd0
    blob=raw(portable/item['file']);assert SHA(blob)==item['sha256']
    rows=list(struct.iter_unpack('<96I',blob));assert len(rows)==256
    assert sum(bool(x[1])for x in rows)==n['selected32'][26]
    summary.append(dict(callback=callback,stage=item['stage'],stageFrame=item['stageFrame'],active=n['selected32'][26]))
    for slot,p in enumerate(rows):
        s=pool[slot*0xd0:(slot+1)*0xd0]
        check('slotState',1,word(s,0x98),p[1],callback,slot)
        if not p[1] or not word(s,0x98):continue
        for index,offset in shot_fields.items():check('shotWords',index,word(s,offset),p[index],callback,slot)
        spec=bytes.fromhex(n['specs'][str(word(s,0xbc))])
        for index,offset,fmt in [(19,0x21,'b'),(20,0x20,'b'),(24,0x22,'h')]:
            check('specFields',index,struct.unpack_from('<'+fmt,spec,offset)[0]&0xffffffff,p[index],callback,slot)
        vm=n['vms'].get(str(slot));check('vmPresent',25,int(vm is not None),p[25],callback,slot)
        if vm is None or not p[25]:
            availability['bothAbsent' if vm is None and not p[25] else 'availabilityDiffers']+=1
            continue
        availability['bothPresent']+=1
        v=bytes.fromhex(vm['rawHex']);assert len(v)==0x5cc
        for index,offset in vm_fields.items():check('vmWords',index,word(v,offset),p[index],callback,slot)
        for index,offset in [(27,0x36),(28,0x4aa)]:
            check('vmIdentity',index,struct.unpack_from('<H',v,offset)[0],p[index],callback,slot)
        mode=(word(v,0x18)>>25)&31;check('vmIdentity',38,mode,p[38],callback,slot)
        if word(v,0x594):missing['parentNotCaptured']+=1;continue
        if mode>3:missing['unsupportedQuadMode']+=1;continue
        m.mem_write(VM,v);m.mem_write(OUTPUT,bytes(48))
        g=bytes.fromhex(n['renderGlobalsRawHex']);m.mem_write(0x4f7a6c,g)
        put(STACK,RETURN);put(STACK+4,OUTPUT)
        m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,VM)
        m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f)
        m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
        m.emu_start(0x479560,RETURN,count=100000);assert m.reg_read(UC_X86_REG_EIP)==RETURN
        quad=struct.unpack('<12I',m.mem_read(OUTPUT,48));quads+=1
        for i,x in enumerate(quad):check('quadWords',68+i,x,p[68+i],callback,slot)
        flt=lambda x:struct.unpack('<f',struct.pack('<I',x))[0]
        left,top=struct.unpack_from('<2i',g,4)
        visible=word(s,0x1c)<10 or any(left<flt(quad[i*3])<left+384 and top<flt(quad[i*3+1])<top+448 for i in range(4))
        check('quadVisibility',67,int(visible),p[67],callback,slot)
out=dict(schema='th14/native-shot-slot-audit/1',allComparedFieldsEqual=not differences,
    snapshotPairs=len(summary),snapshots=summary,comparedFields=dict(compared),differenceCounts=dict(counts),
    geometryVms=quads,vmAvailability=dict(availability),uncomparedGeometry=dict(missing),extraNativeSnapshotsNotAccepted=len(ni['snapshots'])-len(summary),
    exactSlotIdentityUsed=True,rawNumericDifferencesNormalized=False,originalGameplaySnapshots=True,
    quadExecutionIsComponentReconstruction=True,quadFpuControlWord=895,
    completeVmMemoryCompared=False,allModesAccepted=False,ordinaryIndependentTimingAccepted=False,
    completeGame=False,nativeEquivalent=False,evidenceBindings=bindings,toolSha256=SHA(Path(__file__).read_bytes()))
(H/'slot-audit.json').write_text(json.dumps(out,indent=2)+'\n')
(H/'slot-audit-private-differences.json').write_text(json.dumps(differences,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items()if k not in ['snapshots','evidenceBindings','toolSha256']}))
raise SystemExit(2 if differences or missing else 0)
