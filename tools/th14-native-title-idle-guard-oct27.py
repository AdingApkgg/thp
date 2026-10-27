"""Execute the original title-idle entry guard before its later menu services.

Declared Title+1c state0 represents initial activation. It skips the idle
increment that state1 performs. No render, RNG, menu or process state is used
as a C++ input; this command only checks the original x86 guard.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,itertools,json,struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ECX,UC_X86_REG_ESP,UC_X86_REG_EIP

ROOT=Path(__file__).resolve().parents[1]


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'artifacts/th14');out.mkdir(parents=True,exist_ok=False)
    storage=load('title_idle_storage',ROOT/'tools/th14-test-storage.py');storage.check_budget(out,100*1024**3,128*1024**2)
    image=load('title_idle_image',ROOT/'tools/th14-loading-lifecycle-evidence-check.py').Image();machine=image.machine()
    stack,title,stop=0x7ff000,0x600100,0x459a6b
    def observe(guest,address,size,user):
        if address==stop:guest.emu_stop()
    machine.hook_add(UC_HOOK_CODE,observe)
    def put(at,value):machine.mem_write(at,struct.pack('<I',value&0xffffffff))
    rows=[]
    for state,idle,held in itertools.product((0,1,2,18),(0,51,231),(0,1,0xffff)):
        put(title+0x1c,state);put(0x4f58bc,idle);put(0x4d6878,held)
        machine.reg_write(UC_X86_REG_ECX,title);machine.reg_write(UC_X86_REG_ESP,stack)
        machine.emu_start(0x459940,0,count=50)
        assert machine.reg_read(UC_X86_REG_EIP)==stop
        value=struct.unpack('<I',machine.mem_read(0x4f58bc,4))[0]
        expected=(0 if held else idle+1)if state==1 else idle
        assert value==expected
        rows.append(dict(titleState=state,idleBefore=idle,heldWord=held,idleAfter=value))
    result=dict(schema='th14/native-title-idle-guard/1',actualGuardCases=len(rows),cases=rows,
        entry=0x459940,stopBeforeLaterMenuServices=stop,originalBytesHex=image.bytes(0x459940,0x12b).hex(),
        originalExecutableSha256=hashlib.sha256(image.data).hexdigest(),originalProcessLaunched=False,
        cppFirstSessionFrameModelsOriginalStateZero=True,sourceSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        completeGame=False,nativeEquivalent=False)
    (out/'run-tool.py').write_bytes(Path(__file__).read_bytes());(out/'native.json').write_text(json.dumps(result,indent=2)+'\n')
    storage.check_budget(out,100*1024**3,128*1024**2);print(json.dumps(dict(actualGuardCases=len(rows),completeGame=False)))


if __name__=='__main__':main()
