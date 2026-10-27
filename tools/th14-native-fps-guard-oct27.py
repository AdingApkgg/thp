"""Execute the retail FPS draw guard with declared mode/ASCII-manager inputs.

Stops before text formatting/enqueue, or at the original return. The actual
title-image comparison establishes the mode4 frontend mapping separately;
other original Supervisor mode mappings are not claimed here.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,itertools,json,struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ECX,UC_X86_REG_ESP,UC_X86_REG_EIP,UC_X86_REG_EAX

ROOT=Path(__file__).resolve().parents[1]

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    out=args.output.resolve();assert out.is_relative_to(ROOT/'artifacts/th14');out.mkdir(parents=True,exist_ok=False)
    storage=load('fps_storage',ROOT/'tools/th14-test-storage.py');storage.check_budget(out,100*1024**3,128*1024**2)
    image=load('fps_image',ROOT/'tools/th14-loading-lifecycle-evidence-check.py').Image();machine=image.machine()
    stack,stop,fps,ascii_=0x7ff000,0x7ff100,0x600100,0x700100
    hits=[]
    def observe(guest,address,size,user):
        if address in (stop,0x42e5ec):hits.append(address);guest.emu_stop()
    machine.hook_add(UC_HOOK_CODE,observe)
    def put(address,value):machine.mem_write(address,struct.pack('<I',value&0xffffffff))
    rows=[]
    for mode,present in itertools.product((-1,0,1,4,7,8,15,16),(False,True)):
        put(0x4d964c,mode);put(0x4db520,ascii_ if present else 0);put(stack,stop)
        machine.mem_write(fps+0x34,struct.pack('<f',60.0))
        machine.reg_write(UC_X86_REG_ECX,fps);machine.reg_write(UC_X86_REG_ESP,stack)
        hits.clear();machine.emu_start(0x42e5c0,0,count=80)
        assert len(hits)==1 and machine.reg_read(UC_X86_REG_EIP)==hits[0]
        visible=hits[0]==0x42e5ec;assert visible==(mode not in (4,15)and present)
        if not visible:assert machine.reg_read(UC_X86_REG_EAX)==1
        rows.append(dict(supervisorMode=mode,asciiManagerPresent=present,reachesTextBody=visible,stopPc=hits[0]))
    result=dict(schema='th14/native-fps-guard/1',actualGuardCases=len(rows),cases=rows,entry=0x42e5c0,
        originalBytesHex=image.bytes(0x42e5c0,0x2c).hex(),originalExecutableSha256=hashlib.sha256(image.data).hexdigest(),
        originalSkipModes=[4,15],textFormattingOrDrawingExecuted=False,originalProcessLaunched=False,
        cppOtherSupervisorMappingsVerified=False,sourceSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        completeGame=False,nativeEquivalent=False)
    (out/'run-tool.py').write_bytes(Path(__file__).read_bytes());(out/'native.json').write_text(json.dumps(result,indent=2)+'\n')
    storage.check_budget(out,100*1024**3,128*1024**2);print(json.dumps(dict(actualGuardCases=len(rows),originalSkipModes=[4,15],completeGame=False)))

if __name__=='__main__':main()
