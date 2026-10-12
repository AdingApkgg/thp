"""TH14 child creation and first-update state from retail code.

Allocation, script-resource binding, registry insertion and handle lookup are
controlled boundaries. Creation/copy/link code and the child's interpreter run
unchanged. This does not assert allocator or registry implementation equivalence.
"""
import hashlib, importlib, json, struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
PARENT,CHILD,CODE,CHILDCODE,FILE,STACK,RETURN=0x70001000,0x70002000,0x70003000,0x70004000,0x70005000,0x7003f000,0x70000000


def main():
    img,table,_=importlib.import_module('th-anm-handlers').handlers(14)
    m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
    m.mem_map(RETURN,0x40000);m.mem_write(0x4854a0,b'\xc3')
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    def floats(p,*v):m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
    def real(p,n):return list(struct.unpack('<'+'f'*n,m.mem_read(p,n*4)))
    registry=[]
    def boundary(machine,address,size,user):
        sp=m.reg_read(UC_X86_REG_ESP)
        if address==0x47fcb0:m.reg_write(UC_X86_REG_EAX,CHILD)
        elif address==0x40af00:
            vm=get(sp+4);assert vm==CHILD and get(sp+8)==1
            put(vm+0x18,7);put(vm+0x1c,get(vm+0x1c)|0x800000)
            put(vm+0x28,CHILDCODE);put(vm+0x38,CHILDCODE);put(vm+0x30,FILE)
            put(vm+0x554,0x4d8f58);put(vm+0x558,1);floats(vm+0x60,1,1,1,1)
            floats(vm+0x4e0,1,3.1415927410125732);put(vm+0x4e8,65536);put(vm+0x580,vm)
        elif address in (0x47e890,0x47e950,0x47e9f0,0x47eab0):
            out=get(sp+4);assert get(sp+8)==CHILD
            put(out,123);m.reg_write(UC_X86_REG_EAX,out);registry.append(hex(address))
        elif address==0x47f420:m.reg_write(UC_X86_REG_EAX,CHILD)
        elif address==0x47007e and m.reg_read(UC_X86_REG_EDI)==PARENT:m.emu_stop()
    for address,cleanup in ((0x47fcb0,0),(0x40af00,8),(0x47e890,8),(0x47e950,8),(0x47e9f0,8),(0x47eab0,8),(0x47f420,0)):
        m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3')
        m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
    m.hook_add(UC_HOOK_CODE,boundary,begin=0x47007e,end=0x47007e)
    def command(op,*args,refs=0):return struct.pack('<hHhH',op,8+4*len(args),0,refs)+b''.join(struct.pack('<I',v&0xffffffff) for v in args)
    cases=[]
    for op in range(500,507):
        for refs in (0,7 if op in (505,506) else 1):
            for inherited in (0,1):
                for program in (0,1,2):
                    m.mem_write(PARENT,bytes(0x700));m.mem_write(CHILD,bytes(0x700));registry.clear()
                    put(PARENT+0x18,7);put(PARENT+0x1c,inherited<<24);put(PARENT+0x24,7);put(PARENT+0x30,FILE);put(PARENT+0x28,CODE);put(PARENT+0x580,PARENT)
                    floats(PARENT+0x59c,12,21,34);floats(PARENT+0x3c,3,5,8);floats(PARENT+0x48,.25,.5,.75)
                    for i,v in enumerate((1,6,9,12)):put(PARENT+0x4ac+i*4,v)
                    floats(PARENT+0x4bc,.25,-.5,.75,1,5.5,-6.25,7.75)
                    put(PARENT+0x4d8,17);put(PARENT+0x4dc,-19);floats(PARENT+0x4e0,1.25,3.5);put(PARENT+0x4e8,256)
                    args=[10000 if refs else 1]
                    if op in (505,506):args += [struct.unpack('<I',struct.pack('<f',v))[0] for v in ((10004.,10005.) if refs else (.25,-.5))]
                    m.mem_write(CODE,command(op,*args,refs=refs))
                    script=command(509) if program else b''
                    if program==2:script+=command(400,*[struct.unpack('<I',struct.pack('<f',v))[0] for v in (10004.,10005.,10006.)],refs=7)
                    script+=command(2)+command(-1);m.mem_write(CHILDCODE,script)
                    floats(0x4d8f58,1);m.mem_write(0x4f5815,b'\0')
                    m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_EBP,STACK)
                    m.reg_write(UC_X86_REG_EDI,PARENT);m.reg_write(UC_X86_REG_EBX,CODE)
                    m.emu_start(table[op],RETURN,count=100000)
                    assert m.reg_read(UC_X86_REG_EIP)==0x47007e,(op,program,hex(m.reg_read(UC_X86_REG_EIP)))
                    cases.append(dict(op=op,refs=refs,inherited=inherited,program=program,registry=registry[:],
                        parent=get(CHILD+0x594)==PARENT,layer=get(CHILD+0x24),flag24=bool(get(CHILD+0x1c)&0x1000000),
                        position=real(CHILD+0x59c,3),script=real(CHILD+0x3c,3),child=real(CHILD+0x4ec,3),rotation=real(CHILD+0x48,3),
                        variables=list(struct.unpack('<16I',m.mem_read(CHILD+0x4ac,64))),linked=get(PARENT+0x584)==CHILD+0x580,
                        stopped=get(CHILD+0x28)==0))
    out=ROOT/'artifacts/th14/child-native.json';out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases),indent=2)+'\n',encoding='utf-8')
    print(f'{len(cases)} original TH14 child-creation/first-update cases observed.')


if __name__=='__main__':main()
