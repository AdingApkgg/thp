"""TH14 movement setters and mode-zero timelines from the retail executable."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
COMMAND_ENTRIES={408:0x426a74,410:0x426a74,409:0x426b7f,411:0x426b7f}
def main():
    img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
    base,owner,code,stack,end=0x70001000,0x70007000,0x70008000,0x7000f000,0x70000000;m.mem_map(end,0x10000)
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    def floats(p,*v):m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
    fields=(0,4,8,0x34,0x38,0x3c,0x18,0x1c,0x20,0x24,0x28,0x2c,0x40)
    args=[]
    def argument(index):return args[index] if 0<=index<len(args) else args[-1]
    def boundary(machine,address,size,user):
        if address==0x47f0a0:m.reg_write(UC_X86_REG_EAX,0)
        else:m.reg_write(UC_X86_REG_EAX if address in (0x483f30,0x42c1d0) else UC_X86_REG_XMM0,argument(get(m.reg_read(UC_X86_REG_ESP)+4)))
    for address in (0x483fc0,0x483f30,0x47f0a0,0x42c1d0,0x42c230):
        m.mem_write(address,b'\xc2\x04\x00');m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
    f32=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
    def initial(n,flags):
        m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
        m.mem_write(base,bytes(0x8000));put(base+0x40ec,owner);put(owner+4,owner+0x100);put(base+0x4054,flags)
        for k,offset in enumerate((0,0x44,0x88,0xcc)):
            values=[-32.125+k*3.25+n*.01,48.5-k*7.5,3.75+k,-.5+k*.25,.625-k*.125,.03125*(k+1),.5+k*.25,-.125+k*.0625,1,2,3,4]
            for field,value in zip(fields,values):floats(base+offset+field,value)
            put(base+offset+0x40,0)
        floats(base+0x3f60,10,100,25,35);floats(base+0x3f58,16,24)
        floats(0x4d8f58,1);floats(0x4d9294,.125,-.25,.5)
    def state():return [get(base+offset+field) for offset in (0,0x44,0x88,0xcc) for field in fields]+[get(base+0x4054)]
    commands=[]
    for op in (400,402,404,406,416,417,420,422,424,428,430,440,442,444,446):
        for n in range(42):
            flags=(0,0x80000,0x20000,0xa0000)[n%4];initial(n,flags)
            put(base+0x88+0x40,0xabc00000+(n%16));put(base+0xcc+0x40,0xdef00000+(n%16))
            before=state();args[:]=[f32((-999999.,-1000000.,-.25,0.,6.75,1000.,3.1415927410125732)[n%7]),f32((-999999.,-1.25,0.,1.125,2.5,999999.)[n%6]),f32(n*.125)]
            if op==424:args[0]=(0,1,2,3,0xffffffff,0xfffffffe,0x80000000)[n%7]
            if op in (420,422):args.extend([f32((-.125,-999999.,1.5)[n%3]),f32((-999999.,-.25,2.5)[n%3]),f32((.5,1.,2.25)[n%3])])
            m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,base);m.reg_write(UC_X86_REG_EDX,owner)
            m.reg_write(UC_X86_REG_ECX,op);m.reg_write(UC_X86_REG_ESI,code);put(code+4,op)
            entry=0x426dbd if op in (420,422) else 0x4266ed if op in (440,442) else 0x42691f if op in (444,446) else 0x42531e if op==424 else 0x425d6c if op in (400,402) else 0x425e36 if op in (416,417) else 0x426343
            try:m.emu_start(entry,0x429c28,count=100000)
            except Exception as error:raise RuntimeError(f'op {op}, case {n}, pc {m.reg_read(UC_X86_REG_EIP):x}, stack {bytes(m.mem_read(m.reg_read(UC_X86_REG_ESP),32)).hex()}') from error
            assert m.reg_read(UC_X86_REG_EIP)==0x429c28
            commands.append(dict(op=op,n=n,initial=before,args=args[:],result=state()))
    timelines=[]
    for n in range(24):
        flags=(0,0x20000,0x4000000,0x4020000)[n%4];initial(n,flags)
        for k,offset in enumerate((0x88,0xcc)):
            floats(base+offset+0x18,(-1,0,.125,1.25,4,20)[n%6]+k*.25);floats(base+offset+0x1c,(-2.5,-.125,0,.5,1.57,2.75)[n%6]-k*.5)
        before=state();rate=(.5,1.,1.25)[n%3];floats(0x4d8f58,rate);frames=[]
        for frame in range(40):
            put(base+0x4054,get(base+0x4054)|0x40000);put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,base)
            m.emu_start(0x4230d0,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end
            result=get(base+0x4054);status=m.reg_read(UC_X86_REG_EAX);frames.append(dict(result=state(),status=status))
            put(base+0x4054,result&~0x40000)
            if status:break
        timelines.append(dict(n=n,rate=rate,initial=before,frames=frames))
    # The per-frame side of the mode table 0x3df0, which the page reaches as soon as a command leaves
    # a record in mode 2 (+0x40 nibble). 0x4230d0 opens with the current-to-previous copy, then
    # `cmp [edi+0x3f0],0` and the per-record nibble test run the records down the same table the
    # commands use - 0x4160 for the nibble, 0x40dc for the 1/100 snap. The rows sweep the nibble
    # on either record (0, 1 and 2), the fields mode 2 reads (velocity, angle, radius, radial) and
    # the flags the frame path reads (camera delta 0x4000000 and the clamp bit).
    mode_timelines=[]
    mode_extra=[]
    for group,patterns in enumerate((((2,0),(0,2),(2,2),(1,0)),((2,4),(4,2),(3,0),(0,3)))):
      for n in range(24):
        flags=(0,0x20000,0x4000000,0x4020000)[n%4];initial(n,flags)
        for k,(offset,mode) in enumerate(zip((0x88,0xcc),patterns[n%4])):
            record=base+offset
            floats(record+0x18,(-1,0,.5,1.25,4,20)[n%6]+k*.25)
            floats(record+0x1c,(-2.5,-.125,0,.5,1.57,2.75)[n%6]-k*.5)
            floats(record+0x20,(.5,1.5,3.25,8,16,-4)[n%6]+k)
            floats(record+0x24,(-3.5,-.25,0,.75,2.5,7)[n%6]-k*.5)
            floats(record+0x28,(.125,1,2.5)[n%3])
            floats(record+0x2c,(.5,1,2)[n%3])
            put(record+0x40,mode)
        before=state();rate=(.5,1.,1.25)[n%3];floats(0x4d8f58,rate);frames=[]
        for frame in range(40):
            put(base+0x4054,get(base+0x4054)|0x40000);put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,base)
            m.emu_start(0x4230d0,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end
            result=get(base+0x4054);status=m.reg_read(UC_X86_REG_EAX);frames.append(dict(result=state(),status=status))
            put(base+0x4054,result&~0x40000)
            if status:break
        row=dict(group=group,n=n,rate=rate,initial=before,flags=flags,
                 modes=[get(base+0x88+0x40),get(base+0xcc+0x40)],frames=frames)
        (mode_extra if group else mode_timelines).append(row)
    def interpolation():
        return [[get(base+offset+field) if field!=0x20 else int(get(base+offset+field)!=0) for field in (0,4,8,12,0x14,0x18,0x1c,0x20,0x24,0x28,0x2c)] for offset in (0x3c8,0x3f8,0x428,0x458)]
    interpolations=[]
    for op in (405,407,429,431,441,443):
        for mirrored in (0,1):
            for mode in (*range(32),-1,80):
                for variant in range(3):
                    n=mode*3+variant;initial(n,mirrored*0x80000)
                    duration=(0,7,35)[variant];rate=(.5,1.,1.25)[variant];floats(0x4d8f58,rate)
                    before=state();args[:]=[duration,mode,f32((-999999.,-2.75,6.5)[mode%3]),f32((-999999.,-1.25,3.25)[mode%3])]
                    m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,base);m.reg_write(UC_X86_REG_EDX,owner)
                    m.reg_write(UC_X86_REG_ECX,op);m.reg_write(UC_X86_REG_ESI,code);put(code+4,op)
                    m.emu_start(0x426749 if op in (441,443) else 0x426425,0x429c28,count=100000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28
                    configured=interpolation();configured_state=state();frames=[]
                    for frame in range(40):
                        put(base+0x4054,get(base+0x4054)|0x40000);put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,base)
                        m.emu_start(0x4230d0,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end
                        status=m.reg_read(UC_X86_REG_EAX);frames.append(dict(result=state(),interpolation=interpolation(),status=status))
                        put(base+0x4054,get(base+0x4054)&~0x40000)
                        if status:break
                    interpolations.append(dict(op=op,n=n,rate=rate,initial=before,args=args[:],configured=configured,configuredState=configured_state,frames=frames))
    # 408/410 install a constant-velocity movement: 0x426a74 picks the record with `cmp cx,ax`
    # (+0x88 for 0x198, +0xcc for everything else), moves the position into the velocity unless the
    # record is already in mode 2, stores the four arguments under the -999999 sentinel rule, sets the
    # mode nibble to 2 and steps the record through the same mode table every frame uses (0x3df0).
    # 409/411 are the sibling dispatch (0x426b7f): the same `cmp cx,si` picks the record, the
    # integer arguments 0 and 1 (0x2c1d0) decide the count and the index, the float arguments 2, 3
    # and 4 (0x2c230) fill the two interpolator records at +0x3f8/+0x458 and +0x488/+0x4cc under the
    # same -999999 sentinel, and the movement record's nibble is set to 2 (and 0x4180 and 0x23750
    # run) only while that count is positive. The instruction 0x19b the th14 demo reaches carries
    # five parameters (length 36: 0x50, 0, 0x-368bdc10, 0x41800000, 0).
    siblings=[]
    for op in (408,410,409,411):
        for n in range(42):
            initial(n,(0,0x80000,0x20000,0xa0000)[n%4])
            for offset in (0x88,0xcc):put(base+offset+0x40,(0,2,4,1,3,7)[n%6])
            before=state()
            if op in (408,410):
                args[:]=[f32((-999999.,-.000435,-7.5,0.,.5,3.1415927410125732,100.)[n%7]),
                         f32((-999999.,.017453292,2.5,0.,-1.25,60.)[n%6]),
                         f32((-999999.,0.,3.,-2.75,40.)[n%5]),
                         f32((-999999.,0.,4.,1.5,-3.)[n%5])]
            else:
                args[:]=[(80,0,0xffffffff,1,-3,16,0)[n%7]&0xffffffff,
                         (0,7,-1,0x50,3)[n%5]&0xffffffff,
                         f32((-999999.,-.000166,0.,.017453292,1.5,-3.,16.)[n%7]),
                         f32((-999999.,0.,16.,.017453292,-2.75,100.)[n%6]),
                         f32((-999999.,0.,16.,-1.25,3.,.5)[n%6])]
            m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,base);m.reg_write(UC_X86_REG_EDX,owner)
            m.reg_write(UC_X86_REG_ECX,op);m.reg_write(UC_X86_REG_ESI,code);put(code+4,op)
            m.emu_start(COMMAND_ENTRIES[op],0x429c28,count=100000)
            if m.reg_read(UC_X86_REG_EIP)!=0x429c28:raise RuntimeError(f'op {op}, case {n}, pc {m.reg_read(UC_X86_REG_EIP):x}')
            siblings.append(dict(op=op,n=n,initial=before,args=args[:],result=state()))
    # 445/447 (0x1bd/0x1bf) are the two members of group 42 and land at 0x426960, the handler the
    # th14 demo stops on. `cmp cx,si` with si=0x1bd picks the movement record (+0x88, else +0xcc)
    # and then the scalar band at +0x3f8 (else +0x458) - the same two Vec2 records the sibling
    # 0x426b7f fills, and the first and third of the four interpolation records the frame function
    # samples. The first float argument (`push 2`, 0x83fc0) is folded through the -999999 sentinel
    # against the record's own +0x18 speed (and against 0.0 when the mode is 7), the start value is
    # that speed itself, the duration is integer argument 0 (`push 0` twice) - a non-positive
    # duration just stores 0 and returns - the mode is integer argument 1, the two tangents are
    # cleared, the band's timer is reset through 0x14350, and the movement nibble is cleared with
    # `and [eax+0x40],0xfffffff0`.
    band_sets=[]
    for op in (445,447):
        for n in range(24):
            flags=(0,0x80000,0x20000,0xa0000,0x4000000)[n%5];initial(n,flags)
            for offset in (0x88,0xcc):put(base+offset+0x40,(0,2,4,1,3,7)[n%6])
            before=state();rate=(.5,1.,1.25)[n%3];floats(0x4d8f58,rate)
            args[:]=[(0,-1,1,7,35,2,0x50)[n%7]&0xffffffff,
                     (0,1,2,3,7,0,0x11)[n%7]&0xffffffff,
                     f32((-999999.,-1000000.,-.25,0.,6.75,1000.,3.1415927410125732)[n%7])]
            m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,base);m.reg_write(UC_X86_REG_EDX,owner)
            m.reg_write(UC_X86_REG_ECX,op);m.reg_write(UC_X86_REG_ESI,code);put(code+4,op)
            m.emu_start(0x426960,0x429c28,count=100000)
            if m.reg_read(UC_X86_REG_EIP)!=0x429c28:raise RuntimeError(f'op {op}, case {n}, pc {m.reg_read(UC_X86_REG_EIP):x}')
            configured=interpolation();configured_state=state();frames=[]
            for frame in range(40):
                put(base+0x4054,get(base+0x4054)|0x40000);put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,base)
                m.emu_start(0x4230d0,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end
                status=m.reg_read(UC_X86_REG_EAX);frames.append(dict(result=state(),interpolation=interpolation(),status=status))
                put(base+0x4054,get(base+0x4054)&~0x40000)
                if status:break
            band_sets.append(dict(op=op,n=n,rate=rate,initial=before,args=args[:],configured=configured,configuredState=configured_state,frames=frames))
    # 700 (0x2bc) at 0x4285eb and 701 (0x2bd) at 0x42864d, the pair the th14 demo stops on in
    # block 0x584 +0x17c (length 36, five parameters, refs 4). Both take integer argument 0 as a
    # slot index and scale it by 0x380 (`lea esi,[eax*8]; sub esi,eax; shl esi,7`), the slot
    # base being the entity's own +0x5a0 for the floats and +0x8e8 for the integers:
    # 700 stores float arguments 1, 2, 3 at slot +0/+4/+8 and float argument 4 at +0x338, and
    # 701 stores integer arguments 1..5 at +0x348..+0x358. Anything else in the imaged region is
    # the control: no bounds check, and the store targets are the only writes.
    slot_fields=[(s,f) for s in (0,1,2,3,5,7) for f in (0,4,8,0x338,0x348,0x34c,0x350,0x354,0x358)]
    slot_rows=[]
    for op,entry in ((700,0x4285eb),(701,0x42864d)):
        for n in range(12):
            initial(n,(0,0x80000,0x20000,0xa0000)[n%4])
            index=(0,1,2,3,7)[n%5]
            if op==700:
                args[:]=[index,f32((-999999.,-2.75,0.,6.5,1000.,.125,3.1415927410125732)[n%7]),
                         f32((-999999.,0.,1.25,-.5,40.)[n%5]),f32((-999999.,0.,2.5,7.75,-3.)[n%5]),
                         f32((-999999.,0.,1.,-1.75,8.)[n%5])]
            else:
                args[:]=[index,(0,-1,3,0x50,7,0xffffffff,0x40000000)[n%7]&0xffffffff,
                         (1,0,2,0x100,0x7fffffff)[n%5]&0xffffffff,
                         (2,3,-1,0x20)[n%4]&0xffffffff,(7,5,4,1)[n%4]&0xffffffff,
                         (0x10,0x11,0,2)[n%4]&0xffffffff]
            before=state()
            m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,base);m.reg_write(UC_X86_REG_EDX,owner)
            m.reg_write(UC_X86_REG_ECX,op);m.reg_write(UC_X86_REG_ESI,code);put(code+4,op)
            m.emu_start(entry,0x429c28,count=100000)
            if m.reg_read(UC_X86_REG_EIP)!=0x429c28:raise RuntimeError(f'op {op}, case {n}, pc {m.reg_read(UC_X86_REG_EIP):x}')
            slot_rows.append(dict(op=op,n=n,index=index,initial=before,args=args[:],result=state(),
                                 values=[get(base+0x5a0+s*0x380+f) for s,f in slot_fields]))
    # 702 (0x2be) at 0x428a49, the next wall and the first *consumer* of the slot record. It
    # memsets a 0x354 stack request, scales integer argument 0 by the same 0x380 (`lea esi,[eax*8];
    # sub esi,eax; shl esi,7`, saved at [esp+0x2c]), copies the slot's body (0xc6 dwords from the
    # record's +0x20) into the request at +0x34, fills the request's +0/+4/+8 from the two
    # twelve-byte per-index triples at +0x3dd8 and +0x3e98 - all of `base + 3*index*4 + offset` -
    # choosing "base + offset, z forced to zero" when the offset's z is above [0x4c19e8] and
    # "base + the object's own +0x44 position" otherwise, and copies more of the record into
    # +0x0c..+0x28, +0x30 |= 1, +0x34c and +0x350. The request pointer is the one argument 0x3a750
    # receives (`push eax; push 0; call 0x3a750`), so the command's whole observable output is that
    # buffer - which is what the hook below records.
    case_rows=[]
    pending=[]
    m.mem_write(0x43a750,b'\xc2\x08\x00')
    m.hook_add(UC_HOOK_CODE,lambda machine,address,size,user:pending.append(get(machine.reg_read(UC_X86_REG_ESP)+8)),begin=0x43a750,end=0x43a750)
    for sample in range(64):
        op=(702,711,713,703)[sample//16];n=sample%16
        flags=(0,0x80000,0x20000,0xa0000)[n%4];initial(n,flags)
        index=(0,1,2,3,7)[n%5]
        for slot in range(8):
            record=base+0x5a0+slot*0x380
            m.mem_write(record,bytes((0x11*(slot+1)+i*7+n)&0xff for i in range(0x380)))
        for k in range(16):
            floats(base+0x3dd8+12*k,(-1.)**k*(1+k*.5),2.5+k*.25,-.5+k)
            floats(base+0x3e98+12*k,(-1.)**k*(.25+k*.125),-3+k*1.5,(-1.)**k*(.5+k*.5))
        floats(base+0x44,float(-(1.5+n*.25)),float(12.5+n*.5),float(7.25-n*.125))
        before=state();args[:]=[index,(0,1,2,3,7)[n%5]]
        m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,base);put(stack+0x1c,base)
        m.reg_write(UC_X86_REG_ECX,op);m.reg_write(UC_X86_REG_ESI,code);put(code+4,op)
        pending.clear()
        m.emu_start(0x428a49 if op==702 else 0x429014 if op==711 else 0x428c3b if op==703 else 0x428e6a,0x429c28,count=200000)
        if m.reg_read(UC_X86_REG_EIP)!=0x429c28:raise RuntimeError(f'op {op}, case {n}, pc {m.reg_read(UC_X86_REG_EIP):x}')
        pointer=pending[-1]
        case_rows.append(dict(op=op,n=n,index=index,args=args[:],initial=before,result=state(),
                             before=[get(base+0x5a0+index*0x380+offset) for offset in (-8,-4)],
                             record=[get(base+0x5a0+index*0x380+4*i) for i in range(0x380//4)],
                             vectors=[get(base+0x3dd8+4*i) for i in range(0xc0//4)]
                                     +[get(base+0x3e98+4*i) for i in range(0xc0//4)],
                             request=[get(pointer+4*i) for i in range((0x374 if op==703 else 0x354)//4)]))

    # 601 (0x259) at 0x427ba9: the same two tables and the same constant and branch as 0x2be, but
    # the result is written to the record's own head (native +0x598 + index*0x380, i.e. the three
    # floats that its +8/+0xc/+0x10 hold) and the handler then calls the bullet spawner 0x4191a0 with
    # the record pointer, bracketed by `[global+0x60] = [edi+0x4068]` and back to zero. The spawner
    # is stubbed with `ret 4` (it takes the one pointer) so the command's own effect is what is left.
    fire_rows=[]
    spawner=[]
    m.mem_write(0x4191a0,b'\xc2\x04\x00')
    m.hook_add(UC_HOOK_CODE,lambda machine,address,size,user:spawner.append(get(machine.reg_read(UC_X86_REG_ESP)+4)),begin=0x4191a0,end=0x4191a0)
    for n in range(16):
        flags=(0,0x80000,0x20000,0xa0000)[n%4];initial(n,flags)
        index=(0,1,2,3,7)[n%5]
        for slot in range(8):
            m.mem_write(base+0x598+slot*0x380,bytes((0x13*(slot+1)+i*5+n)&0xff for i in range(0x380)))
        for k in range(16):
            floats(base+0x3dd8+12*k,(-1.)**k*(1+k*.5),2.5+k*.25,-.5+k)
            floats(base+0x3e98+12*k,(-1.)**k*(.25+k*.125),-3+k*1.5,(-1.)**k*(.5+k*.5))
        floats(base+0x44,float(-(1.5+n*.25)),float(12.5+n*.5),float(7.25-n*.125))
        m.mem_write(0x4db530,(owner).to_bytes(4,'little'))
        before=state();args[:]=[index,(0,1,2,3,7)[n%5]]
        m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,base);put(stack+0x1c,base)
        m.reg_write(UC_X86_REG_ECX,0x259);put(code+4,0x259)
        spawner.clear()
        m.emu_start(0x427ba9,0x429c28,count=200000)
        if m.reg_read(UC_X86_REG_EIP)!=0x429c28:raise RuntimeError(f'op 601, case {n}, pc {m.reg_read(UC_X86_REG_EIP):x}')
        pointer=spawner[-1]
        fire_rows.append(dict(n=n,index=index,args=args[:],initial=before,result=state(),
                             before=[get(base+0x598+index*0x380),get(base+0x598+index*0x380+4)],
                             record=[get(base+0x598+index*0x380+4*i) for i in range(0x380//4)],
                             offset=pointer-base,
                             head=[get(base+0x598+index*0x380+4*i) for i in range(0x380//4)],
                             vectors=[get(base+0x3dd8+4*i) for i in range(0xc0//4)]
                                     +[get(base+0x3e98+4*i) for i in range(0xc0//4)]))
    random_rows=[]
    positions=((-40,80),(40,80),(10,80),(10,100),(10,120),(3.75,91.25),(16.25,108.75),(0,110),(20,90),(10,100),(10,100),(10,100))
    for op in (412,413):
      for mode in (0,4,7,17,*range(18,32),-1,80):
       for duration in (0,7,35):
        for variant,(x,y) in enumerate(positions):
          initial(variant,0);rate=(.5,1,1.25)[variant%3];floats(0x4d8f58,rate)
          floats(base+0x44,x,y);put(0x4db67c,owner);floats(owner+0x5e0,(-20.,10.,40.)[variant%3])
          seed=variant*5177;put(0x4db510,seed);put(0x4db514,0);before=state()
          args[:]=[duration,mode,f32((0.,-1.25,3.5)[variant%3])]
          m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,base);m.reg_write(UC_X86_REG_ECX,op)
          m.emu_start(0x427289,0x429c28,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28
          configured=interpolation();configured_state=state();rng=[get(0x4db510)&65535,get(0x4db514)];frames=[]
          for frame in range(12):
            put(base+0x4054,get(base+0x4054)|0x40000);put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,base)
            m.emu_start(0x4230d0,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end
            status=m.reg_read(UC_X86_REG_EAX);frames.append(dict(result=state(),interpolation=interpolation(),status=status))
            put(base+0x4054,get(base+0x4054)&~0x40000)
            if status:break
          random_rows.append(dict(op=op,rate=rate,player=(-20.,10.,40.)[variant%3],seed=seed,initial=before,args=args[:],configured=configured,configuredState=configured_state,rng=rng,frames=frames))
    position_rows=[]
    def position_bands():
        return [[int(get(base+off+field)!=0) if field==0x48 else get(base+off+field)
                 for field in (*range(0xc,0x3c,4),0x3c,0x40,0x44,0x48,0x4c,0x50,0x60)]
                for off in (0x2f8,0x360)]
    for op in (401,403,425,426,427):
      for mode in ((*range(32),-1,80) if op in (401,403) else range(18)):
       for variant in range(9):
        n=mode*9+variant;initial(n,(0,0x80000,0x4000000)[variant%3]);rate=(.5,1,1.25)[variant%3]
        floats(0x4d8f58,rate);before=state()
        args[:]=[(0,7,35)[variant//3],mode,f32((-999999.,-80.,24.5)[variant%3]),f32((100.,-999999.,72.125)[variant%3])]
        m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,base);m.reg_write(UC_X86_REG_EDX,owner)
        m.reg_write(UC_X86_REG_ECX,op);m.reg_write(UC_X86_REG_ESI,code);put(code+4,op)
        if op in (425,426,427):args[:]=[(-1,0,35)[variant//3],f32(1.25),f32(-2.5),args[2],args[3],f32(-3.75),f32(.625)]
        m.emu_start(0x4261c6 if op in (425,426,427) else 0x425eb6,0x429c28,count=100000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28
        configured=position_bands();configured_state=state();frames=[]
        for frame in range(76):
            put(base+0x4054,get(base+0x4054)|0x40000);put(stack,end)
            m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,base)
            m.emu_start(0x4230d0,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end
            status=m.reg_read(UC_X86_REG_EAX);frames.append(dict(result=state(),bands=position_bands(),status=status))
            put(base+0x4054,get(base+0x4054)&~0x40000)
            if status:break
        position_rows.append(dict(op=op,n=n,rate=rate,initial=before,args=args[:],configured=configured,configuredState=configured_state,frames=frames))
    out=ROOT/'artifacts/th14/enemy-movement-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),randomRows=random_rows,positionRows=position_rows,commands=commands,timelines=timelines,modeTimelines=mode_timelines,modeTimelinesExtra=mode_extra,interpolations=interpolations,bandSets=band_sets,caseRows=case_rows,fireRows=fire_rows,spawner=dict(entry=0x43a750,stub='ret 8'),slotFields=[list(pair) for pair in slot_fields],slotRows=slot_rows,siblings=siblings),indent=2)+'\n',encoding='utf-8')
    print(f'{len(commands)} movement setters, {sum(len(r["frames"]) for r in timelines)} mode-zero frame states, {len(siblings)} constant-velocity/mode records, {sum(len(r["frames"]) for r in mode_timelines)} mode-0/1/2 frame states, {sum(len(r["frames"]) for r in mode_extra)} mode-3/4 frame states observed, {len(band_sets)} band sets, {len(slot_rows)} slot rows, {len(case_rows)} laser-request rows, {len(fire_rows)} op-601 rows.')
if __name__=='__main__':main()
