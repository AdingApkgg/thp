"""Execute the complete retail D3D9 device-selection owner with COM calls observed."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
    img=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
    assert hashlib.sha256(img.data).hexdigest()=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        page=base&~4095;m.mem_map(page,((base+size+4095)&~4095)-page);m.mem_write(base,img.data[raw:raw+n])
    base,end,call,stack,present,d3d,table,device=0x70000000,0x70000100,0x70000200,0x7001f000,0x70001000,0x70002000,0x70003000,0x70004000
    m.mem_map(base,0x20000)
    put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
    get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
    put(d3d,table);put(table+0x40,call);m.mem_write(call,b'\xc2\x1c\x00')
    requests=[];responses=[]
    def observe(machine,address,size,user):
        sp=machine.reg_read(UC_X86_REG_ESP);words=[get(sp+4+i*4) for i in range(7)]
        assert words[0]==d3d and words[1]==0 and words[3]==0x12345678 and words[5]==present and words[6]==0x4d8f68
        result=responses[len(requests)];requests.append(dict(adapter=words[1],deviceType=words[2],behaviorFlags=words[4],result=result))
        if not result:put(words[6],device)
        machine.reg_write(UC_X86_REG_EAX,result)
    m.hook_add(UC_HOOK_CODE,observe,begin=call,end=call)
    rows=[];failure=0x8876086c
    cases=[('hardware',0,[0],[(1,0x40)]),('software-fallback',0,[failure,0],[(1,0x40),(1,0x20)]),('reference-fallback',0,[failure,failure,0],[(1,0x40),(1,0x20),(2,0x20)]),('forced-reference',2,[0],[(2,0x20)]),('all-failed',0,[failure]*3,[(1,0x40),(1,0x20),(2,0x20)]),('forced-reference-failed',2,[failure],[(2,0x20)])]
    for name,flags,results,expected in cases:
        requests.clear();responses[:]=results;put(0x4d8f64,d3d);put(0x4d8f68,0);put(0x4d916c,flags);put(0x4d9684,0xa4);put(0x4f5a18,0x12345678)
        put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,present)
        m.emu_start(0x46b110,end,count=10000);assert m.reg_read(UC_X86_REG_EIP)==end
        assert [(r['deviceType'],r['behaviorFlags']) for r in requests]==expected
        result=m.reg_read(UC_X86_REG_EAX);assert result==(1 if results[-1] else 0)
        final=get(0x4d9684);assert final==(0xa5 if name=='hardware' else 0xa4)
        rows.append(dict(name=name,configFlags=flags,requests=requests.copy(),returnValue=result,selectedHardware=bool(final&1),finalModeFlags=final))
    report=dict(passed=True,completeGame=False,nativeEquivalent=False,entry='0x46b110',executableSha256=hashlib.sha256(img.data).hexdigest(),functionSha256=hashlib.sha256(img.read(0x46b110,0x90)).hexdigest(),toolSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),rows=rows,scope='Whole retail device-selection function; only CreateDevice COM return boundary controlled. Default HAL hardware vertex processing first, then HAL software, then REF software; explicit compatibility flag skips HAL.',limits=['Not an observed original-game live device creation','Controlled HRESULTs establish branch behavior, not driver success','Existing software-vertex GPU fixtures remain valid for that tested device mode only'])
    (ROOT/'docs/porting/th14-device-create-native-verified-oct11.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(f'Passed {len(rows)} whole retail device-selection cases')
if __name__=='__main__':main()
