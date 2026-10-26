"""Execute retail ECL554's actual call and run-mode guard with declared inputs.

Stops before the guarded resource/creation body, or at its skip epilogue.
No original process, UI, audio or complete callback/animation is executed.
"""
from pathlib import Path
import argparse, hashlib, importlib.util, itertools, json, struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EIP

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();out=args.output.resolve()
    assert out.is_relative_to(ROOT/'artifacts/th14') and not out.exists()
    out.mkdir(parents=True)
    storage_spec=importlib.util.spec_from_file_location('logo_storage',ROOT/'tools/th14-test-storage.py')
    storage=importlib.util.module_from_spec(storage_spec);storage_spec.loader.exec_module(storage)
    storage.check_budget(out,100*1024**3,128*1024**2)
    spec=importlib.util.spec_from_file_location('logo_image',ROOT/'tools/th14-loading-lifecycle-evidence-check.py')
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    image=helper.Image();machine=image.machine()
    stops=[]
    def observe(guest,address,size,user):
        if address in (0x434e35,0x434edb):
            stops.append(address);guest.emu_stop()
    machine.hook_add(UC_HOOK_CODE,observe)
    rows=[]
    for mode,flags in itertools.product((-1,0,8,9),(0,2,0x12,0x22,0x40,0x42,0xff)):
        machine.mem_write(0x4d964c,struct.pack('<I',mode&0xffffffff))
        machine.mem_write(0x4f58b8,struct.pack('<I',flags))
        machine.reg_write(UC_X86_REG_ESP,0x7ff000)
        stops.clear();machine.emu_start(0x425577,0,count=80)
        assert len(stops)==1 and machine.reg_read(UC_X86_REG_EIP)==stops[0]
        rows.append(dict(mode=mode,flags=flags,stopPc=stops[0],entersCreationBody=stops[0]==0x434e35))
    report=dict(schema='th14/ecl554-native-guard/1',cases=rows,
        originalExecutableSha256=hashlib.sha256(image.data).hexdigest(),
        actualEclCallPc=0x425577,actualCallee=0x434e10,
        callBytesHex=image.bytes(0x425577,5).hex(),guardBytesHex=image.bytes(0x434e10,0x25).hex(),
        stopsBeforeResourceAndCreation=True,realOriginalProcessLaunched=False,
        minimumFreeBytes=100*1024**3,maximumObservationBytes=128*1024**2,
        sourceSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        completeGame=False,nativeEquivalent=False)
    (out/'run-tool.py').write_bytes(Path(__file__).read_bytes())
    (out/'native.json').write_text(json.dumps(report,indent=2)+'\n')
    storage.check_budget(out,100*1024**3,128*1024**2)
    print(json.dumps(dict(cases=len(rows),actualNativeGuard=True,completeGame=False)))

if __name__=='__main__':main()
