"""Read the retail replay manager without advancing its cursor or inferring EOF."""
import struct

FIELDS=('status','manager','mode','selectedStage','header','inputPointer','fpsPointer',
        'cursor','managerCallbackCount','declaredFrames','stageAndSeed','payloadBytes',
        'nextInputFirstFourBytes','nextInputLastTwoBytes')
STRIDE=4*len(FIELDS)


def snapshot(read):
 u32=lambda address:struct.unpack('<I',read(address,4))[0]
 words=[0]*len(FIELDS);manager=u32(0x4db688);words[1]=manager
 if not manager:return struct.pack('<14I',*words)
 words[0]=1;words[2]=u32(manager+0x10);words[3]=u32(manager+0x218)
 words[8]=u32(manager+0x210)
 if words[2]!=1:return struct.pack('<14I',*words)
 words[0]|=2
 if not 1<=words[3]<=6:return struct.pack('<14I',*words)
 words[0]|=4;slot=manager+words[3]*40
 words[4:8]=[u32(slot+offset)for offset in (0xd8,0xcc,0xd4,0xdc)]
 if not words[4]:return struct.pack('<14I',*words)
 words[0]|=8
 stage_seed,frames,payload=struct.unpack('<3I',read(words[4],12));words[9:12]=frames,stage_seed,payload
 # 4551f3 uses signed comparison and skips the read on exhaustion. Do likewise:
 # do not dereference the next-frame pointer once the declared range is exhausted.
 signed=lambda value:value if value<0x80000000 else value-0x100000000
 if words[5]and 0<=signed(words[7])<signed(frames):
  words[12:14]=struct.unpack('<2I',read(words[5],6)+b'\0\0');words[0]|=16
 return struct.pack('<14I',*words)
