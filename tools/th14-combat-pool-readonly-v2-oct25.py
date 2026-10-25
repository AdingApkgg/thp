"""Read-only TH14 combat snapshots at an already suspended Player boundary.

This module never attaches, suspends, writes, launches or reads UI state. The
owning hardware observer supplies ReadProcessMemory. Keep original raw object
bytes alongside selected semantic words; no numeric difference is normalized.
"""
import gzip
import hashlib
import json
import struct

ENEMY_FIELDS = [('instance',0x11e4),('health',0x5164),('maxHealth',0x5168),('score',0x5160),('flags',0x5244)]
for name,base in [('current',0x1234),('absolute',0x1278),('relative',0x12bc)]:
    ENEMY_FIELDS += [(name+'.'+key,base+off) for key,off in [('x',0),('y',4),('z',8),('vx',0x34),('vy',0x38),('vz',0x3c)]]
ENEMY_FIELDS += [(name+'.'+key,base+off) for name,base in [('current',0x1234),('absolute',0x1278),('relative',0x12bc)] for key,off in [('speed',0x18),('angle',0x1c)]]
ENEMY_FIELDS += [('immunity',0x51e0),('timer2bc',0x14b0)]
BULLET_FIELDS = [('state',0xc0e),('flags',0x20),('collisionDelay',0x24),('x',0xbc0),('y',0xbc4),('z',0xbc8),('vx',0xbcc),('vy',0xbd0),('vz',0xbd4),('speed',0xbd8),('angle',0xbdc),('hitboxX',0xbe0),('hitboxY',0xbe4),('lifetime',0x13c4),('spriteColor',0x13ec),('activeTransforms',0xc04),('sizeCurrent',0x139c),('size',0x13bc)]
SHOT_FIELDS = [('slot',None),('state',0x98),('timerPrevious',0x18),('timerCurrent',0x1c),('timerFraction',0x20),('flags',0x10),('animation',0x14),('x',0x54),('y',0x58),('z',0x5c),('speed',0x6c),('angle',0x70),('vx',0x88),('vy',0x8c),('vz',0x90),('collisionWidth',0xb0),('damage',0xac),('hitThis',0xa4),('hitLast',0xa8)]
AREA_FIELDS = [('slot',None),('flags',0x10),('radius',0x14),('angle',0x1c),('width',0x24),('height',0x28),('x',0x2c),('y',0x30),('z',0x34),('timerPrevious',0x70),('timerCurrent',0x74),('timerFraction',0x78),('growth',0x18),('angularVelocity',0x20),('damage',0x84),('total',0x88),('maximum',0x8c),('period',0x90),('stamp',0x94)]
ITEM_FIELDS = [('slot',None),('state',0xbf0),('type',0xbf4),('displayType',0xbf8),('x',0xbac),('y',0xbb0),('z',0xbb4),('vx',0xbb8),('vy',0xbbc),('vz',0xbc0),('lifetimeFraction',0xbd0),('attractionSpeed',0xbfc),('delay',0xc00)]
SCHEMA = dict(enemies=ENEMY_FIELDS,bullets=BULLET_FIELDS,shots=SHOT_FIELDS,areas=AREA_FIELDS,items=ITEM_FIELDS)

def selected(blob, fields, slot=None):
    return [slot if off is None else struct.unpack_from('<H' if name=='state' and fields is BULLET_FIELDS else '<I',blob,off)[0] for name,off in fields]

def due(callback, frame):
    return callback==1 or callback%997==0 or callback in (26000,30000,36000,38900,60000,90000,120000) or frame in (0,1,900,3000,4500,4577)

def capture(read, callback, words, directory):
    assert callback>0 and len(words)==32
    assert 0<=words[27]<3 and 0<=words[28]<2 and 0<=words[29]<5
    assert due(callback,words[0])
    u32=lambda address:struct.unpack('<I',read(address,4))[0]
    rows={name:[] for name in SCHEMA}
    original={name:[] for name in SCHEMA}
    player=u32(0x4db67c);assert player
    player_raw=read(player,0x184c0)
    def record(name, address, blob, slot=None):
        rows[name].append(selected(blob,SCHEMA[name],slot))
        original[name].append(dict(address=address,slot=slot,rawHex=blob.hex()))
    for name,manager_address,head_offset,size,capacity in [('enemies',0x4db544,0xd0,0x530c,1000),('bullets',0x4db530,0x80,0x13f4,2000)]:
        manager=u32(manager_address);node=u32(manager+head_offset) if manager else 0;visited=set()
        while node:
            assert node not in visited and len(visited)<capacity,(name,hex(node),len(visited))
            visited.add(node);address=u32(node);assert address
            record(name,address,read(address,size))
            node=u32(node+4)
        if name=='enemies' and manager:assert len(rows[name])==u32(manager+0xd8)
    for slot in range(256):
        offset=0x6c8+slot*0xd0;blob=player_raw[offset:offset+0xd0]
        if struct.unpack_from('<I',blob,0x98)[0]:record('shots',player+offset,blob,slot)
        offset=0xde18+slot*0xa4;blob=player_raw[offset:offset+0xa4]
        if struct.unpack_from('<I',blob,0x10)[0]&1:record('areas',player+offset,blob,slot)
    manager=u32(0x4db660)
    if manager:
        pool=read(manager+0x14,4696*0xc18)
        for slot in range(4696):
            offset=slot*0xc18
            if struct.unpack_from('<I',pool,offset+0xbf0)[0]:record('items',manager+0x14+offset,pool[offset:offset+0xc18],slot)
    data=dict(schema='th14/combat-pool-checkpoint/1',readOnly=True,boundary='before original Player callback',callback=callback,stage=words[30],stageFrame=words[0],selected32=words,fields=SCHEMA,rows=rows,original=original,playerAddress=player,playerRawHex=player_raw.hex(),bulletOrder='original active linked list; no sorting or numeric normalization',completeGame=False,nativeEquivalent=False)
    raw=(json.dumps(data,separators=(',',':'))+'\n').encode()
    directory.mkdir(exist_ok=True)
    output=directory/f'callback-{callback:06}.json.gz';assert not output.exists()
    compressed=gzip.compress(raw,mtime=0);output.write_bytes(compressed)
    return dict(callback=callback,stage=words[30],stageFrame=words[0],counts={n:len(v) for n,v in rows.items()},file=output.name,bytes=len(compressed),sha256=hashlib.sha256(compressed).hexdigest())
