"""Read bounded original shot/VM bytes at an already paused Player boundary.

The caller owns the process and supplies ReadProcessMemory. This module never
attaches, launches, writes process memory, calls game code or changes threads.
"""
import gzip
import hashlib
import json
import struct

WINDOWS = {2: [(2142,2146),(5509,5517),(6284,6300)],
           3: [(1475,1482),(2081,2098)]}
# The broad stage2 final window retains intervening frames, too.


def due(callback, stage, frame):
    return callback in (1,1000) or any(a<=frame<=b for a,b in WINDOWS.get(stage,[]))


def find_vm(read, manager, handle):
    """Read the actual 47f0a0 pool/list algorithm without invoking it."""
    u32=lambda p:struct.unpack('<I',read(p,4))[0]
    if not handle:return 0
    slot=handle&0x1fff
    if slot!=0x1fff:
        p=manager+slot*0x5e4
        return p+0xdc if read(p+0x6b8,1)!=b'\0' and u32(p+0x61c)==handle else 0
    seen=set()
    for offset in (0xfe8208,0xfe8210):
        node=u32(manager+offset)
        while node:
            assert node not in seen and len(seen)<8192
            seen.add(node);vm=u32(node)
            assert vm and vm+0x570==node
            if u32(vm+0x540)==handle:return vm
            node=u32(node+4)
    return 0


def capture(read, callback, words, directory):
    assert due(callback,words[30],words[0])
    u32=lambda p:struct.unpack('<I',read(p,4))[0]
    player=u32(0x4db67c);manager=u32(0x4f56cc)
    assert player and manager
    pool=read(player+0x6c8,256*0xd0)
    active=[];vms={};specs={}
    for slot in range(256):
        shot=pool[slot*0xd0:(slot+1)*0xd0]
        w=lambda offset:struct.unpack_from('<I',shot,offset)[0]
        if not w(0x98):continue
        active.append(slot)
        handle=w(0x14);vm=find_vm(read,manager,handle)
        if vm:
            data=read(vm,0x5cc)
            assert struct.unpack_from('<I',data,0x540)[0]==handle
            vms[str(slot)]=dict(handle=handle,address=vm,rawHex=data.hex())
        spec=w(0xbc)
        if spec and str(spec)not in specs:specs[str(spec)]=read(spec,0x40).hex()
    assert len(active)==words[26]
    data=dict(schema='th14/native-shot-lifetime/1',callback=callback,stage=words[30],stageFrame=words[0],
        boundary='before original Player',readOnly=True,nativeValuesProvidedToEngine=False,
        selected32=words,playerAddress=player,shotPoolRawHex=pool.hex(),activeSlots=active,
        vms=vms,specs=specs,renderGlobalsRawHex=read(0x4f7a6c,0x24).hex(),
        completeGame=False,nativeEquivalent=False)
    blob=gzip.compress((json.dumps(data,separators=(',',':'))+'\n').encode(),mtime=0)
    directory.mkdir(exist_ok=True)
    path=directory/('callback-'+str(callback).zfill(6)+'.json.gz')
    assert not path.exists();path.write_bytes(blob)
    return dict(callback=callback,stage=words[30],stageFrame=words[0],activeSlots=len(active),
        resolvedVms=len(vms),file=path.name,bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest())
