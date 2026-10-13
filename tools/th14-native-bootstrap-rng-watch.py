"""Observe original emulated RNG writes for one frame; no state modifications.

Diagnostics only. Stack words are return-address candidates, not an independently
unwound call stack. The parent backend's own scope and failures remain intact.
"""
import hashlib
import importlib
import json
from pathlib import Path
import struct
import sys
from unicorn import UC_HOOK_MEM_WRITE
from unicorn.x86_const import UC_X86_REG_EIP,UC_X86_REG_ESP

RUN = importlib.import_module('th14-native-bootstrap-run')
ROOT = RUN.ROOT
SHA = lambda data: hashlib.sha256(data).hexdigest()


def main():
    def take(name):
        index = sys.argv.index(name)
        value = sys.argv[index+1]
        del sys.argv[index:index+2]
        return value
    frame,output = int(take('--watch-frame')),(ROOT/take('--watch-output')).resolve()
    if not 1 <= frame <= 200000 or not output.is_relative_to(ROOT/'artifacts/th14'):
        raise ValueError('Explicit frame and private diagnostic output required.')
    source = Path(RUN.__file__).read_bytes()
    native_constructor,records = RUN.Uc,[]
    def constructor(*args,**kwargs):
        machine = native_constructor(*args,**kwargs)
        get = lambda address: struct.unpack('<I',machine.mem_read(address,4))[0]
        def observed(uc,access,address,size,value,user):
            control = get(0x4db558)
            if not control or get(control+0x14) != frame:return
            sp,pc = uc.reg_read(UC_X86_REG_ESP),uc.reg_read(UC_X86_REG_EIP)
            words = list(struct.unpack('<64I',uc.mem_read(sp,256)))
            records.append(dict(frame=frame,address=hex(address),bytes=size,value=value,pc=hex(pc),
                                beforeHex=bytes(uc.mem_read(address,size)).hex(),stackPointer=hex(sp),
                                stackWords=[hex(word) for word in words],
                                gameReturnCandidates=[dict(offset=index*4,address=hex(word)) for index,word in enumerate(words) if 0x400000 <= word < 0x4b0000]))
        machine.hook_add(UC_HOOK_MEM_WRITE,observed,begin=0x4db510,end=0x4db517)
        return machine
    RUN.Uc = constructor
    try:
        RUN.main()
    finally:
        RUN.Uc = native_constructor
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps(dict(diagnosticOnly=True,completeGame=False,nativeEquivalent=False,frame=frame,
            observerSha256=SHA(Path(__file__).read_bytes()),parentSourceSha256=SHA(source),writes=records,
            scope='Read-only memory-write observer on original executable replay RNG during one emulated frame. No candidate data or state writes; parent backend remains experimental beyond independent retail validation. Raw stack words retained, no call-stack certification.'),indent=2)+'\n',encoding='utf-8')
        output.with_suffix('.parent.py').write_bytes(source)
        print('RNG observations:',len(records),output,flush=True)


if __name__ == '__main__':main()
