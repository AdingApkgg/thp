"""Execute retail 4567a0/456b20 defaults; only memset is controlled."""
import hashlib, importlib, itertools, json, struct, sys
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT = Path(__file__).resolve().parents[1]

def main():
    img, _, _ = importlib.import_module('th-anm-handlers').handlers(14)
    m = Uc(UC_ARCH_X86, UC_MODE_32)
    for _, b, size, raw, n in img.sections:
        start = b & ~4095
        m.mem_map(start, ((b + size + 4095) & ~4095) - start)
        m.mem_write(b, img.data[raw:raw+n])
    m.mem_map(0x70000000, 0x50000)
    bank, timing, stack, ret = 0x70001000, 0x70010000, 0x7004d000, 0x7004e000
    def put(p, v): m.mem_write(p, struct.pack('<I', v & 0xffffffff))
    def get(p): return struct.unpack('<I', m.mem_read(p, 4))[0]
    def memset(machine, a, size, user):
        sp = machine.reg_read(UC_X86_REG_ESP)
        target, value, length = (get(sp+n) for n in (4, 8, 12))
        machine.mem_write(target, bytes([value & 255])*length)
        machine.reg_write(UC_X86_REG_EAX, target)
    m.mem_write(0x48f980, b'\xc3')
    m.hook_add(UC_HOOK_CODE, memset, begin=0x48f980, end=0x48f980)
    def run(a):
        put(stack, ret)
        m.reg_write(UC_X86_REG_ESP, stack)
        m.reg_write(UC_X86_REG_ECX, bank)
        m.emu_start(a, ret, count=100000)
        assert m.reg_read(UC_X86_REG_EIP) == ret
    run(0x4567a0)
    initial = bytes(m.mem_read(bank, 0x5298)).hex()
    def timestamp(machine, a, size, user):
        sp = machine.reg_read(UC_X86_REG_ESP)
        machine.mem_write(get(sp+4), struct.pack('<Q', 0x123456789abcdef0))
    m.mem_write(0x486553, b'\xc3')
    m.hook_add(UC_HOOK_CODE, timestamp, begin=0x486553, end=0x486553)
    insertions = []
    for difficulty, score, stage, continues, ratio in itertools.product((0, 1, 4, 5), (0, 9999, 10000, 50000, 50001, 100000, 100001, 0x7fffffff, 0x80000000, 0xffffffff), (1, 7, 9), (0, 257), (0, .125, 1)):
        m.mem_write(bank, bytes.fromhex(initial))
        for rank in range(60): m.mem_write(bank+0x10+rank*28+15, bytes([rank+8]))
        for p,v in ((0x4f5834,difficulty),(0x4f5830,score),(0x4f58a4,stage),(0x4f5838,continues),(0x4db54c,timing)): put(p,v)
        m.mem_write(timing+0x24, struct.pack('<dd', ratio, 1.0))
        run(0x447e00)
        rank = struct.unpack('<i',struct.pack('<I',m.reg_read(UC_X86_REG_EAX)))[0]
        insertions.append(dict(difficulty=difficulty,score=score,stage=stage,continues=continues,ratio=ratio,rank=rank,rows=bytes(m.mem_read(bank+0x10,60*28)).hex()))
    cases = []
    for seed, calls in itertools.product((0, 1, 904, 0x5678, 0x9630, 0xffff), (0, 97, 0x80000000, 0xffffffff)):
        put(0x4db510, seed); put(0x4db514, calls)
        put(0x4db508, 0x1234); put(0x4db50c, 987)
        run(0x456b20)
        assert get(0x4db508) == 0x1234 and get(0x4db50c) == 987
        cases.append(dict(seed=seed, calls=calls, finalSeed=get(0x4db510), finalCalls=get(0x4db514), settings=bytes(m.mem_read(bank, 0x42c)).hex()))
    out = ROOT/'artifacts/th14/score-native.json'
    # Run the complete original writer through real checksum/LZSS/encryption.
    # Stop before path/OS I/O; allocator and memcpy are explicit boundaries.
    m.mem_map(0x71000000, 0x800000)
    manager, header, heap = 0x71001000, 0x71040000, 0x71100000
    allocation = [heap]
    def allocate(machine, a, size, user):
        length=get(machine.reg_read(UC_X86_REG_ESP)+4)
        p=allocation[0];allocation[0]=(p+length+15)&~15
        assert allocation[0]<0x71800000
        machine.reg_write(UC_X86_REG_EAX,p)
    def copy(machine,a,size,user):
        sp=machine.reg_read(UC_X86_REG_ESP)
        dst,src,length=(get(sp+n) for n in (4,8,12))
        machine.mem_write(dst,bytes(machine.mem_read(src,length)))
        machine.reg_write(UC_X86_REG_EAX,dst)
    for address,callback in ((0x485540,allocate),(0x487620,copy)):
        m.mem_write(address,b'\xc3')
        m.hook_add(UC_HOOK_CODE,callback,begin=address,end=address)
    m.mem_write(0x4855d2,b'\xc3') # workspace emulator free; allocations remain mapped
    for index in range(7): m.mem_write(manager+8+index*0x5298,bytes.fromhex(initial))
    m.mem_write(manager+0x24230,bytes.fromhex(next(r['settings'] for r in cases if r['seed']==904 and r['calls']==0)))
    m.mem_write(header,struct.pack('<6I',0x31344854,0,5,0x100,0,0))
    put(manager,header);put(0x4db68c,manager);put(stack,ret)
    m.reg_write(UC_X86_REG_ESP,stack)
    def invalid(machine, access, address, size, value, user):
        print('unmapped',hex(address),'ip',hex(machine.reg_read(UC_X86_REG_EIP)),'sp',hex(machine.reg_read(UC_X86_REG_ESP)),flush=True)
        return False
    m.hook_add(UC_HOOK_MEM_INVALID,invalid)
    # Actual44ac80..44acdc name commit, before ANM/menu transition.
    name_cases=[];overlay=0x71050000;name_buffer=0x71051000
    for selection,difficulty,rank,text in itertools.product((0,2,5,6),(0,1,4),(0,5,9),('', 'A', 'ABCDEFGH')):
        row=manager+8+selection*0x5298+0x10+(difficulty*10+rank)*28
        m.mem_write(row,bytes(range(28)))
        m.mem_write(manager+0x24230+12,b'0123456789')
        m.mem_write(name_buffer,text.encode()+b'\0');put(overlay+0x38,rank)
        put(0x4f5828,selection//2);put(0x4f582c,selection%2)
        m.reg_write(UC_X86_REG_EDI,overlay);m.reg_write(UC_X86_REG_ESI,name_buffer)
        m.reg_write(UC_X86_REG_ECX,difficulty*5);m.reg_write(UC_X86_REG_ESP,stack)
        m.emu_start(0x44ac80,0x44acdc,count=1000)
        assert m.reg_read(UC_X86_REG_EIP)==0x44acdc
        name_cases.append(dict(selection=selection,difficulty=difficulty,rank=rank,name=text,row=bytes(m.mem_read(row,28)).hex(),lastName=bytes(m.mem_read(manager+0x24230+12,10)).hex()))
    # Restore defaults after controlled name-commit probes.
    for index in range(7): m.mem_write(manager+8+index*0x5298,bytes.fromhex(initial))
    m.mem_write(manager+0x24230,bytes.fromhex(next(r['settings'] for r in cases if r['seed']==904 and r['calls']==0)))
    def writer(label):
        allocation[0]=heap
        put(stack,ret);m.reg_write(UC_X86_REG_ESP,stack)
        m.emu_start(0x456f60,0x457086,count=100000000)
        for part in range(30):
            if m.reg_read(UC_X86_REG_EIP)==0x457086: break
            m.emu_start(m.reg_read(UC_X86_REG_EIP),0x457086,count=100000000)
        assert m.reg_read(UC_X86_REG_EIP)==0x457086, hex(m.reg_read(UC_X86_REG_EIP))
        packed=m.reg_read(UC_X86_REG_EDI)
        native_file=bytes(m.mem_read(header,24))+bytes(m.mem_read(packed,get(header+16)))
        raw=bytes(m.mem_read(manager+8,0x24654))
        (ROOT/f'artifacts/th14/score-native-{label}.dat').write_bytes(native_file)
        (ROOT/f'artifacts/th14/score-native-{label}.raw').write_bytes(raw)
        return raw
    raw=writer('default')
    # Nonempty normal/practice records, long128-byte names and opaque fields.
    character_record=manager+8+5*0x5298
    spell=character_record+0x978+119*0x9c
    m.mem_write(spell,(b'oracle '+b'A'*90).ljust(128,b'\0'))
    for offset,value in ((0x80,99),(0x84,12),(0x88,345),(0x8c,678),(0x98,1234567)):put(spell+offset,value)
    put(character_record+0x7b8,73);put(character_record+0x7bc,123456)
    put(character_record+0x7c4,123);put(character_record+0x7e0,2)
    put(character_record+0x7f0+(7+4*8)*8,24680)
    m.mem_write(character_record+0x7f4+(7+4*8)*8,b'\x01\x11')
    m.mem_write(character_record+0x10+6*0x118,b'opaque total row')
    m.mem_write(manager+0x24230+12,b'PLAYER\0  ')
    writer('records')
    if len(sys.argv)>1:
        assert sys.argv[1]=='--load' and len(sys.argv) in (3,4)
        raw=Path(sys.argv[3]).read_bytes() if len(sys.argv)==4 else raw
        port_file=Path(sys.argv[2]).read_bytes()
        assert len(port_file)==struct.unpack_from('<I',port_file,4)[0]
        m.mem_write(header,port_file);m.mem_write(manager+8,b'\x5a'*len(raw))
        put(manager,header);put(manager+4,0);put(stack,ret)
        m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,manager)
        m.emu_start(0x456de0,ret,count=100000000)
        assert m.reg_read(UC_X86_REG_EIP)==ret
        assert bytes(m.mem_read(manager+8,len(raw)))==raw,'retail456de0 loaded records'
        (ROOT/'artifacts/th14/score-native-load.json').write_text(json.dumps(dict(passed=True,executableSha256=hashlib.sha256(img.data).hexdigest(),portFileSha256=hashlib.sha256(port_file).hexdigest(),decodedBytes=len(raw),referenceRawSha256=hashlib.sha256(raw).hexdigest(),scope='Retail456de0 decryption, decompression, record checksum/version and full record loading. Allocator, free, memcpy and memset controlled; no filesystem I/O.'))+'\n',encoding='utf-8')
    out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(), initial=initial, cases=cases, insertions=insertions, names=name_cases), separators=(',', ':'))+'\n', encoding='utf-8')
    print(f'Native TH14 full defaults, {len(cases)} settings RNG cases and {len(insertions)} rankings')
if __name__ == '__main__': main()
