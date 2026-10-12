"""Run TH14 registry traversal with controlled VM-update and deletion boundaries."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
BASE,MANAGER,STACK,RETURN=0x70000000,0x71000000,0x700ff000,0x700fe000


def main():
    img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
    m.mem_map(BASE,0x100000);m.mem_map(MANAGER,0x1000000)
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    updates=[];deleted=[];config=[]
    def boundary(machine,address,size,user):
        p=machine.reg_read(UC_X86_REG_ECX) if address==0x46fe50 else get(machine.reg_read(UC_X86_REG_ESP)+4)
        i=(p-BASE)//0x1000
        if address==0x46fe50:
            updates.append(i);put(p+0x24,config[i]['nextLayer']);machine.reg_write(UC_X86_REG_EAX,config[i]['status'])
        else:deleted.append(i)
    for address,cleanup in ((0x46fe50,0),(0x47eb50,4)):
        m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
    cases=[]
    for overlay in range(2):
        for start in range(36):
            for variant in range(3):
                config.clear();updates.clear();deleted.clear()
                for layer in range(36):put(MANAGER+0xfe8218+layer*0x5cc+0x590,BASE+0x9000)
                for i in range(8):
                    p=BASE+i*0x1000;node=p+0x800;m.mem_write(p,bytes(0x900))
                    row=dict(layer=(start+i*7)%34,nextLayer=(start+i*7+variant)%(40 if overlay else 34),
                             status=1 if variant==1 and i%3==0 else 0,retired=variant==2 and i%3==1)
                    config.append(row);put(p+0x24,row['layer']);put(p+0x1c,0x20 if row['retired'] else 0)
                    put(node,p);put(node+4,BASE+(i+1)*0x1000+0x800 if i<7 else 0)
                put(MANAGER+(0xfe8210 if overlay else 0xfe8208),BASE+0x800);m.mem_write(0x4f5815,b'\0')
                put(STACK,RETURN);m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,MANAGER)
                m.emu_start(0x47e6c0 if overlay else 0x47e5e0,RETURN,count=100000);assert m.reg_read(UC_X86_REG_EIP)==RETURN
                layers=[]
                for layer in range(36):
                    p=get(MANAGER+0xfe8218+layer*0x5cc+0x590);values=[]
                    while p:
                        if p==BASE+0x9000:values.append(-1);break
                        values.append((p-BASE)//0x1000);assert len(values)<=8;p=get(p+0x590)
                    layers.append(values)
                cases.append(dict(overlay=overlay,start=start,variant=variant,config=list(config),updates=list(updates),deleted=list(deleted),layers=layers))
    (ROOT/'artifacts/th14/layers-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases),separators=(',',':'))+'\n',encoding='utf-8')
    print(f'Observed {len(cases)} native TH14 registry walks.')


if __name__=='__main__':main()
