"""Retail sound enqueue/pan/stop and queue processing, controlled COM outputs."""
import hashlib, importlib, json, struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
    img,*_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,b,size,raw,n in img.sections:
        p=b&~4095;m.mem_map(p,((b+size+4095)&~4095)-p);m.mem_write(b,img.data[raw:raw+n])
    base=0x70000000;m.mem_map(base,0x100000);stack=base+0xf0000;vtable=base+0x1000;events=[]
    # Whole46f190/46f160 resolve the first table word by voice ID for loading.
    # Enqueue46e3d0 instead reads metadata at table[id] (preserve that quirk).
    voice_rows={img.u32(0x4d61b8+n*20):0x4d61b8+n*20 for n in range(76)}
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    def bits(v):return struct.unpack('<I',struct.pack('<f',v))[0]
    offsets={0x24:('status',8),0x48:('stop',4),0x34:('position',8),0x40:('pan',8),0x3c:('volume',8),0x30:('play',16)}
    def hook(uc,a,n,u):
        sp=uc.reg_read(UC_X86_REG_ESP);off=a-(base+0x10000);kind,pop=offsets[off];voice=(get(sp+4)-(base+0x2000))//0x100
        if kind=='status':put(get(sp+8),1)
        else:events.append([kind,voice,get(sp+16) if kind=='play' else get(sp+8) if kind!='stop' else 0])
        uc.reg_write(UC_X86_REG_EAX,0);uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+pop)
    for off in offsets:put(vtable+off,base+0x10000+off);m.hook_add(UC_HOOK_CODE,hook,begin=base+0x10000+off,end=base+0x10000+off)
    def call(address,args=(),x=0,stop=None,owner=0):
        m.mem_write(stack,struct.pack('<'+str(len(args)+1)+'I',base,*[v&0xffffffff for v in args]));m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EBP,0);m.reg_write(UC_X86_REG_ECX,owner);m.reg_write(UC_X86_REG_XMM2,bits(x));m.reg_write(UC_X86_REG_MXCSR,0x1f80)
        m.emu_start(address,stop or base,count=100000);assert m.reg_read(UC_X86_REG_EIP)==(stop or base)
    def reset(master=100,enabled=1,present=1):
        events.clear();m.mem_write(0x4f7b74,struct.pack('<12i',*[-1]*12));m.mem_write(0x4f7ba4,bytes(12*4+12*128*4));m.mem_write(0x4f95dc,bytes(76*24))
        for voice in range(76):
            record=0x4f95dc+voice*24;obj=base+0x2000+voice*0x100;put(obj,vtable);put(record,obj if present else 0);put(record+4,-1);put(record+8,voice_rows[voice])
        put(0x4fd1b0,master);m.mem_write(0x4d9152,bytes([enabled]));m.mem_write(0x4f5815,b'\0')
    def state():
        return dict(indices=list(struct.unpack('<12I',m.mem_read(0x4f7b74,48))),counts=list(struct.unpack('<12I',m.mem_read(0x4f7ba4,48))),pans=list(struct.unpack('<1536I',m.mem_read(0x4f7bd4,6144))),metadata=[get(0x4f95e0+n*24) for n in range(76)])
    rows=[]
    def sequence(ops):
        reset()
        for op in ops:
            if op[0]=='enqueue':call(0x46e3d0,(op[1],op[2]))
            elif op[0]=='positioned':call(0x46e470,(op[1],),op[2])
            else:call(0x46e550,(op[1],))
        rows.append(dict(operations=ops,state=state()))
    for voice in range(76):
        for count in (1,59,60,61,128):sequence([['enqueue',voice,177]]*count)
        for x in (-192.0001,-192,-1.99999,-.0001,0,.0001,1.99999,192,192.0001,16777216):sequence([['positioned',voice,x]])
        sequence([['enqueue',voice,4],['positioned',voice,96],['stop',voice],['enqueue',voice,9]])
    sequence([['enqueue',n,0] for n in range(13)])
    sequence([['enqueue',n,0] for n in range(12)]+[['stop',75],['enqueue',0,0]])
    outputs=[]
    for voice in range(76):
        for master in (0,1,7,33,50,99,100,101):
            reset(master);call(0x46e470,(voice,),96);initial=state();events.clear()
            # Complete queue loop, excludes earlier asynchronous BGM controller.
            m.reg_write(UC_X86_REG_ESP,stack);call(0x46ea0c,stop=0x46eae5)
            outputs.append(dict(voice=voice,master=master,enabled=1,present=1,stop=False,positioned=True,initial=initial,state=state(),events=events[:]))
        for enabled,present,stopped in ((0,1,False),(1,0,False),(1,1,True)):
            reset(100,enabled,present);call(0x46e3d0,(voice,0))
            if stopped:call(0x46e550,(voice,))
            initial=state();events.clear();call(0x46ea0c,stop=0x46eae5)
            outputs.append(dict(voice=voice,master=100,enabled=enabled,present=present,stop=stopped,positioned=False,initial=initial,state=state(),events=events[:]))
    music=[];controller=base+0x90000;holder=base+0x91000
    for master in range(102):
        for volume in (0,-1,-100,-300,-499,-880,-1000,-1500,-2500,-3000,-4000,-4999,-5000,-5001,-10000):
            reset();put(0x4fd1ac,master);put(controller+4,holder);put(holder,base+0x2000);events.clear();call(0x481200,(volume,),owner=controller)
            assert len(events)==1 and events[0][:2]==['volume',0]
            music.append(dict(master=master,volume=volume,result=events[0][2]))
    result=dict(passed=True,queueCases=len(rows),outputCases=len(outputs),rows=rows,outputs=outputs,music=music,executableSha256=hashlib.sha256(img.data).hexdigest(),scope='Whole46e3d0 enqueue,46e470 positioned and nonnegative46e550 stop. Complete46ea0c..46eae5 queue processing and whole46eb30 play wrapper with controlled DirectSound COM status/stop/position/pan/volume/play outputs. All76 valid voice IDs,60 aggregation cap, full12-slot queue, mixed stopped/requeued entries, float pan and eight master-volume inputs, disabled/missing-buffer/stop states. Whole481200 music-volume setter covers102 master levels and15 base/fade volume values. Voice records resolve IDs as46f190; enqueue metadata preserves raw table indexing. No invalid native voice indexing, music controller/thread scheduling, COM failures or PCM/device equivalence claim.')
    (ROOT/'artifacts/th14/sound-queue-native.json').write_text(json.dumps(result)+'\n',encoding='utf-8');print(f'PASS {len(rows)} native sound queue cases / {len(outputs)} native output cases / {len(music)} music volume cases')
if __name__=='__main__':main()
