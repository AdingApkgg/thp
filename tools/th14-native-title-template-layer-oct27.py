"""Execute the original title factory prefix with declared allocation/copy services.

Stop at the real ANM update entry. The template's layer is an explicit service
input; its interpreter and registry publication are not executed by this test.
An existing actual-native title snapshot independently supplies the layer0 case.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,itertools,json,struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_ECX,UC_X86_REG_ESP,UC_X86_REG_EIP

ROOT=Path(__file__).resolve().parents[1]


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'artifacts/th14');out.mkdir(parents=True,exist_ok=False)
    storage=load('title_layer_storage',ROOT/'tools/th14-test-storage.py');storage.check_budget(out,100*1024**3,128*1024**2)
    image=load('title_layer_image',ROOT/'tools/th14-loading-lifecycle-evidence-check.py').Image();u=image.machine()
    stack,title,resource,vm=0x7ff000,0x600100,0x620000,0x640000
    current={};calls=[];stopped=[]
    def put(at,value):u.mem_write(at,struct.pack('<I',value&0xffffffff))
    def word(at):return struct.unpack('<I',u.mem_read(at,4))[0]
    def finish_service(result,arguments):
        sp=u.reg_read(UC_X86_REG_ESP);pc=word(sp)
        u.reg_write(UC_X86_REG_EAX,result);u.reg_write(UC_X86_REG_ESP,sp+4+arguments)
        u.reg_write(UC_X86_REG_EIP,pc)
    def observe(guest,pc,size,user):
        if pc==0x47fcb0:
            calls.append(dict(service='declared-allocation',entry=pc));finish_service(vm,0)
        elif pc==0x40af00:
            sp=u.reg_read(UC_X86_REG_ESP);assert word(sp+4)==vm and word(sp+8)==current['script']
            assert u.reg_read(UC_X86_REG_ECX)==resource
            u.mem_write(vm,b'\0'*0x5cc);put(vm+0x24,current['layer'])
            calls.append(dict(service='declared-template-prefix-copy',entry=pc,layer=current['layer']))
            finish_service(vm,8)
        elif pc==0x46fe50:
            assert u.reg_read(UC_X86_REG_ECX)==vm;stopped.append(pc);u.emu_stop()
    u.hook_add(UC_HOOK_CODE,observe);rows=[]
    for script,layer in itertools.product((0,86,91),(0,7,22,35)):
        current.update(script=script,layer=layer);calls.clear();stopped.clear()
        put(title+0x14,resource);put(resource+0x134,0);put(0x4f5815,0)
        put(stack,0x7ff100);put(stack+4,script)
        u.reg_write(UC_X86_REG_ECX,title);u.reg_write(UC_X86_REG_ESP,stack)
        u.emu_start(0x458d70,0,count=120)
        assert stopped==[0x46fe50]and word(vm+0x24)==layer and word(resource+0x134)==1
        assert word(vm+0x1c)==0x200 and len(calls)==2
        rows.append(dict(script=script,templateLayer=layer,layerAtActualAnmUpdate=word(vm+0x24),services=list(calls)))
    report=dict(actualFactoryPrefixCases=len(rows),entry=0x458d70,stopBeforeAnmUpdate=0x46fe50,
        allocationAndTemplateCopyAreDeclaredServices=True,actualAnmUpdateExecuted=False,actualRegistryPublicationExecuted=False,
        originalProcessLaunched=False,cases=rows,originalExecutableSha256=hashlib.sha256(image.data).hexdigest(),
        originalFactoryPrefixHex=image.bytes(0x458d70,0x8a).hex(),
        sourceSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),completeGame=False,nativeEquivalent=False)
    (out/'run-tool.py').write_bytes(Path(__file__).read_bytes());(out/'native.json').write_text(json.dumps(report,indent=2)+'\n')
    storage.check_budget(out,100*1024**3,128*1024**2);print(json.dumps(dict(actualFactoryPrefixCases=len(rows),completeGame=False)))


if __name__=='__main__':main()
