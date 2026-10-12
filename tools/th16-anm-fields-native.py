"""Execute TH16 ANM field handlers at their own dispatch boundary.

Only mode-10 initialization (469e20) is recorded instead of executed; its
allocation/geometry semantics are outside this state comparison.
"""
import hashlib, importlib, json, struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *
ROOT = Path(__file__).resolve().parents[1]
VM, CODE, STACK, RETURN, LOOP = 0x70001000, 0x70003000, 0x7001f000, 0x70000000, 0x45fb9a

def main():
    img, table, default = importlib.import_module('th-anm-handlers').handlers(16)
    m = Uc(UC_ARCH_X86, UC_MODE_32)
    for _, base, size, raw, count in img.sections:
        start = base & ~4095
        m.mem_map(start, ((base + size + 4095) & ~4095) - start)
        m.mem_write(base, img.data[raw:raw+count])
    m.mem_map(RETURN, 0x20000)
    m.mem_write(0x47499b, b'\xc3')
    m.mem_write(0x469e20, b'\xc3')
    m.mem_write(0x477fa7,b'\xb8'+struct.pack('<I',0x70008000)+b'\xc3')
    callback = [0]
    m.hook_add(UC_HOOK_CODE, lambda machine, address, size, data: callback.__setitem__(0, callback[0]+1), begin=0x469e20, end=0x469e20)
    def put(p,v): m.mem_write(p,struct.pack('<I',v & 0xffffffff))
    def get(p): return struct.unpack('<I',m.mem_read(p,4))[0]
    rows=[]
    values=[-257,-1,0,1,2,3,7,8,10,15,16,18,19,20,21,23,24,29,31,32,35,36,42,43,63,255,256,0x20001,0x30002]
    seeds=[(0,0),(0xffffffff,0xffffffff),(0xab123457,0x78345678),(0x4c800007,0x820100)]
    ops=(302,303,304,312,313,421,438,507,305,306,307,310,311,314,315,419,423,424,431,432,437)
    for op in ops:
        for seed, (flags,flags2) in enumerate(seeds):
            for value in values:
                for second in (-1,0,1,2,3,8):
                    for refs in range(4 if op==312 else 2):
                        m.mem_write(VM,bytes(0x700));m.mem_write(CODE,bytes(64))
                        put(VM+0x4a0,value);put(VM+0x4a4,second);put(VM+0x18,27);put(VM+0x28,CODE);put(VM+0x530,flags);put(VM+0x534,flags2)
                        size=16 if op==312 else 12
                        m.mem_write(CODE,struct.pack('<hHhHii',op,size,0,refs,10000 if refs&1 else value,10001 if refs&2 else second))
                        callback[0]=0
                        for reg,val in [(UC_X86_REG_ESP,STACK),(UC_X86_REG_EBP,STACK),(UC_X86_REG_EBX,VM),(UC_X86_REG_EDI,CODE),(UC_X86_REG_FPCW,0x37f),(UC_X86_REG_FPSW,0),(UC_X86_REG_FPTAG,0xffff),(UC_X86_REG_MXCSR,0x1f80)]:m.reg_write(reg,val)
                        m.emu_start(table[op],LOOP,count=100000)
                        assert m.reg_read(UC_X86_REG_EIP)==LOOP
                        rows.append(dict(op=op,seed=seed,refs=refs,value=value,second=second,flags=flags,flags2=flags2,afterFlags=get(VM+0x530),afterFlags2=get(VM+0x534),layer=get(VM+0x18),advance=get(VM+0x28)-CODE,mode10Calls=callback[0]))
    shapes=[]
    for op in (603,604,605,606,607,608,611,612,613):
        for flags,_ in seeds:
            for value in (-257,-1,0,1,3,255,256,4096):
                for second in (-19,0,1,33):
                    for refs in range(8):
                        m.mem_write(VM,bytes(0x700));m.mem_write(CODE,bytes(64));put(VM+0x28,CODE);put(VM+0x530,flags)
                        circle=op in (604,605)
                        put(VM+0x4a0,-257);m.mem_write(VM+0x74,struct.pack('<f',-2.5));m.mem_write(VM+0x4b0,struct.pack('<ffff',-1.25,.125,448,-99));m.mem_write(CODE,struct.pack('<hHhHf',op,20 if op==611 else 16,0,refs,10004 if refs&1 else value));m.mem_write(CODE+12,struct.pack('<i' if circle else '<f',(10000 if circle else 10005) if refs&2 else second))
                        if op==611:put(CODE+16,10000 if refs&4 else 16)
                        for reg,val in [(UC_X86_REG_ESP,STACK),(UC_X86_REG_EBP,STACK),(UC_X86_REG_EBX,VM),(UC_X86_REG_EDI,CODE)]:m.reg_write(reg,val)
                        m.emu_start(table[op],LOOP,count=100000);assert m.reg_read(UC_X86_REG_EIP)==LOOP
                        shapes.append(dict(op=op,flags=flags,value=value,second=second,refs=refs,words=[get(VM+o) for o in (0x530,0x70,0x74,0x4a0)]))
    flips=[]
    for op in (308,309):
        for flags,_ in seeds:
            for value in (-2.75,-0.0,0.0,1.5,1e-45):
                m.mem_write(VM,bytes(0x700));m.mem_write(CODE,struct.pack('<hHhH',op,8,0,0));put(VM+0x28,CODE);put(VM+0x530,flags);m.mem_write(VM+0x50,struct.pack('<ff',value,-2.5))
                for reg,val in [(UC_X86_REG_ESP,STACK),(UC_X86_REG_EBX,VM),(UC_X86_REG_EDI,CODE),(UC_X86_REG_XMM1,0xbf800000)]:m.reg_write(reg,val)
                m.emu_start(table[op],LOOP,count=100000);assert m.reg_read(UC_X86_REG_EIP)==LOOP
                flips.append(dict(op=op,flags=flags,valueBits=struct.unpack('<I',struct.pack('<f',value))[0],words=[get(VM+o) for o in (0x530,0x50,0x54)]))
    pivots=[]
    for value in (-257,-1,0,1,3,255,256,4096):
        for second in (-19,0,1,33):
            for refs in range(4):
                m.mem_write(VM,bytes(0x700));put(VM+0x28,CODE);put(VM+0x530,0xab123457);put(VM+0x534,0x78345678)
                m.mem_write(VM+0x4b0,struct.pack('<ffff',-1.25,.125,448,-99));m.mem_write(CODE,struct.pack('<hHhHff',436,16,0,refs,10004 if refs&1 else value,10005 if refs&2 else second))
                for reg,val in [(UC_X86_REG_ESP,STACK),(UC_X86_REG_EBP,STACK),(UC_X86_REG_EBX,VM),(UC_X86_REG_EDI,CODE)]:m.reg_write(reg,val)
                m.emu_start(table[436],LOOP,count=100000);assert m.reg_read(UC_X86_REG_EIP)==LOOP
                pivots.append(dict(value=value,second=second,refs=refs,words=[get(VM+o) for o in (0x80,0x84,0x530,0x534)]))
    rings=[]
    for op in (600,601,602):
        for flags,_ in seeds:
            for value in (-257,-1,0,1,2,16,256,32767,1073741824):
                for refs in (0,1):
                    m.mem_write(VM,bytes(0x700));put(VM+0x28,CODE);put(VM+0x530,flags);put(VM+0x4a0,value);m.mem_write(CODE,struct.pack('<hHhHi',op,12,0,refs,10000 if refs else value))
                    for reg,val in [(UC_X86_REG_ESP,STACK),(UC_X86_REG_EBP,STACK),(UC_X86_REG_EBX,VM),(UC_X86_REG_EDI,CODE)]:m.reg_write(reg,val)
                    m.emu_start(table[op],LOOP,count=100000);assert m.reg_read(UC_X86_REG_EIP)==LOOP
                    rings.append(dict(op=op,flags=flags,value=value,refs=refs,words=[get(VM+0x530),get(VM+0x5bc),int(get(VM+0x5b8)==0x70008000)]))
    report=dict(title=16,executableSha256=hashlib.sha256(img.data).hexdigest(),scope='Twenty-one retail field handlers, rectangle/circle/ellipse initializers, scale flips, pivot setter and ring/arc allocation requests at next-dispatch boundary. Shape dimensions and pivot resolve the first four float variables; circle segment count and ring size resolve integer variables. Flips include signed zero and subnormals. Mode-10 geometry initializer is a recorded boundary. Ring allocation wrapper executes with malloc returning a fixed controlled pointer; production request environment is controlled. Production tail geometry and screen-UV hooks are controlled. No native allocator, animation tail, pivot transform, geometry vertices, shape renderer or full gameplay claim.',handlers={str(op):hex(table[op]) for op in (*ops,308,309,436,600,601,602,603,604,605,606,607,608,611,612,613)},noops=[op for op in range(max(table)+1) if table.get(op,default)==default],cases=rows,shapes=shapes,flips=flips,pivots=pivots,rings=rings)
    out=ROOT/'artifacts/th16/anm-fields-native.json';out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,separators=(',',':'))+'\n',encoding='utf-8')
    print(f'{len(rows)} TH16 native ANM field cases')

if __name__=='__main__':main()
