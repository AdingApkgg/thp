"""Read captured heap metadata using the actual captured ntdll RtlSizeHeap code.

An isolated emulated clone is used; no live game handle or candidate state input.
"""
import argparse,gzip,hashlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda data:hashlib.sha256(data).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--snapshot',required=True)
    p.add_argument('--heap',type=lambda x:int(x,0),required=True);p.add_argument('--pointer',action='append',type=lambda x:int(x,0),default=[])
    p.add_argument('--all-virtual',action='store_true')
    a=p.parse_args();directory=(ROOT/a.snapshot).resolve()
    assert directory.is_relative_to(ROOT/'artifacts/th14')
    manifest=json.loads((directory/'manifest.json').read_text());context=(directory/'context.bin').read_bytes()
    assert SHA((directory/'memory.bin.gz').read_bytes())==manifest['memorySha256']
    assert SHA(context)==manifest['contextSha256'] and len(context)==716
    m=Uc(UC_ARCH_X86,UC_MODE_32)
    with gzip.open(directory/'memory.bin.gz','rb') as stream:
        for region in manifest['regions']:
            data=stream.read(region['bytes']);assert SHA(data)==region['sha256']
            m.mem_map(region['base'],region['bytes']);m.mem_write(region['base'],data)
        assert not stream.read(1)
    get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
    put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def string(p):
        data=bytearray()
        for index in range(256):
            b=m.mem_read(p+index,1)[0]
            if not b:return data.decode('ascii')
            data.append(b)
        raise ValueError('Unbounded captured export name')
    exports={};module_base=None
    for base in sorted({r['allocation'] for r in manifest['regions'] if r['kind']==0x1000000}):
        if bytes(m.mem_read(base,2))!=b'MZ':continue
        pe=base+get(base+0x3c);magic=struct.unpack('<H',m.mem_read(pe+0x18,2))[0]
        if magic!=0x10b:continue
        export=get(pe+0x78)
        if not export or string(base+get(base+export+12)).lower()!='ntdll.dll':continue
        module_base=base;table=base+export
        functions,names,ordinals=[base+get(table+offset) for offset in (28,32,36)]
        for index in range(get(table+24)):
            name=string(base+get(names+index*4))
            ordinal=struct.unpack('<H',m.mem_read(ordinals+index*2,2))[0]
            exports[name]=base+get(functions+ordinal*4)
    assert module_base and 'RtlSizeHeap' in exports
    sp=struct.unpack_from('<I',context,196)[0]
    tebs=[]
    for region in manifest['regions']:
        if region['kind']!=0x20000:continue
        for page in range(region['base'],region['base']+region['bytes'],4096):
            if get(page+0x18)==page and get(page+0x20)==manifest['pid'] and get(page+8)<=sp<get(page+4):tebs.append(page)
    assert len(tebs)==1;teb=tebs[0];selector=struct.unpack_from('<I',context,144)[0]
    arena=0x40000000;assert not any(r['base']<arena+0x10000 and arena<r['base']+r['bytes'] for r in manifest['regions'])
    m.mem_map(arena,0x10000);gdt=arena+0x1000
    descriptor=0xfff|((teb&0xffff)<<16)|(((teb>>16)&255)<<32)|(0xf3<<40)|(4<<52)|(((teb>>24)&255)<<56)
    m.mem_write(gdt+(selector>>3)*8,struct.pack('<Q',descriptor))
    for sel,access in [(8,0x9b),(16,0x93)]:m.mem_write(gdt+sel,struct.pack('<Q',0xffff|(access<<40)|(15<<48)|(12<<52)))
    m.reg_write(UC_X86_REG_GDTR,(0,gdt,4095,0));m.reg_write(UC_X86_REG_CS,8)
    for name in ('SS','DS','ES'):m.reg_write(globals()['UC_X86_REG_'+name],16)
    m.reg_write(UC_X86_REG_FS,selector)
    rows=[]
    if a.all_virtual:
        assert get(a.heap+0x60)==0xeeffeeff
        head=a.heap+0x9c;node=get(head);previous=head;seen=set()
        while node!=head:
            assert node not in seen and len(seen)<256 and get(node+4)==previous
            seen.add(node);a.pointer.append(node+32);previous,node=node,get(node)
        assert get(head+4)==previous
    assert a.pointer
    for pointer in a.pointer:
        stack=arena+0xf000;put(stack,arena);put(stack+4,a.heap);put(stack+8,1);put(stack+12,pointer)
        m.reg_write(UC_X86_REG_ESP,stack)
        m.emu_start(exports['RtlSizeHeap'],arena,count=100000,timeout=1000000)
        assert m.reg_read(UC_X86_REG_EIP)==arena,hex(m.reg_read(UC_X86_REG_EIP))
        size=m.reg_read(UC_X86_REG_EAX);assert size!=0xffffffff
        rows.append(dict(heap=hex(a.heap),pointer=hex(pointer),nativeBytes=size,entryBytesHex=bytes(m.mem_read(pointer-32,32)).hex()))
    result=dict(passed=True,nativeEquivalent=False,completeGame=False,rows=rows,
                nativeEntry=hex(exports['RtlSizeHeap']),nativeEntryPrefixSha256=SHA(bytes(m.mem_read(exports['RtlSizeHeap'],256))),
                snapshotManifestSha256=SHA((directory/'manifest.json').read_bytes()),toolSha256=SHA(Path(__file__).read_bytes()),
                scope='Actual captured ntdll RtlSizeHeap(heap,HEAP_NO_SERIALIZE,pointer), invoked in a private cloned snapshot. No candidate or heap-size model supplies the expected return. This is a local heap metadata proof, not complete-game or host allocator equivalence.')
    out=directory/'heap-size-probe-oct13.json';out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))

if __name__=='__main__':main()
