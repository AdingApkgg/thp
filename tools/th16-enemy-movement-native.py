"""TH14 movement setters and mode-zero timelines from the retail executable."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
COMMAND_ENTRIES={408:0x426a74,410:0x426a74,409:0x426b7f,411:0x426b7f}
def main():
    img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
    base,owner,code,stack,end=0x70001000,0x70007000,0x70008000,0x7000f000,0x70000000;m.mem_map(end,0x20000)
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    def floats(p,*v):m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
    fields=(0,4,8,0x34,0x38,0x3c,0x18,0x1c,0x20,0x24,0x28,0x2c,0x40)
    args=[]
    def argument(index):return args[index] if 0<=index<len(args) else args[-1]
    def boundary(machine,address,size,user):
        if address==0x46efa0:m.reg_write(UC_X86_REG_EAX,0)
        else:m.reg_write(UC_X86_REG_EAX if address in (0x473c90,0x4251d0) else UC_X86_REG_XMM0,argument(get(m.reg_read(UC_X86_REG_ESP)+4)))
    for address in (0x473d40,0x473c90,0x46efa0,0x4251d0,0x425200):
        m.mem_write(address,b'\xc2\x04\x00');m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
    f32=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
    def initial(n,flags):
        m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
        m.mem_write(base,bytes(0x8000));put(base+0x44b8,owner);put(owner+0xc,owner+0x100);put(0x490eb0,0x4a5788);put(owner+4,owner+0x100);put(base+0x4060,flags)
        for k,offset in enumerate((0,0x44,0x88,0xcc)):
            values=[-32.125+k*3.25+n*.01,48.5-k*7.5,3.75+k,-.5+k*.25,.625-k*.125,.03125*(k+1),.5+k*.25,-.125+k*.0625,1,2,3,4]
            for field,value in zip(fields,values):floats(base+offset+field,value)
            put(base+offset+0x40,0)
        floats(base+0x3f60,10,100,25,35);floats(base+0x3f58,16,24)
        floats(0x4a5788,1);floats(0x4c140c,.125,-.25,.5)
        put(stack+0x2000-0x438,0x88)
    def state():return [get(base+offset+field) for offset in (0,0x44,0x88,0xcc) for field in fields]+[get(base+0x4060)]
    commands=[]
    for op in (400,402,404,406,416,417,420,422,424,428,430,440,442,444,446):
        for n in range(42):
            flags=(0,0x80000,0x20000,0xa0000)[n%4];initial(n,flags)
            put(base+0x88+0x40,0xabc00000+(n%16));put(base+0xcc+0x40,0xdef00000+(n%16))
            before=state();args[:]=[f32((-999999.,-1000000.,-.25,0.,6.75,1000.,3.1415927410125732)[n%7]),f32((-999999.,-1.25,0.,1.125,2.5,999999.)[n%6]),f32(n*.125)]
            if op==424:args[0]=(0,1,2,3,0xffffffff,0xfffffffe,0x80000000)[n%7]
            if op in (420,422):args.extend([f32((-.125,-999999.,1.5)[n%3]),f32((-999999.,-.25,2.5)[n%3]),f32((.5,1.,2.25)[n%3])])
            m.reg_write(UC_X86_REG_EBP,stack+0x2000);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,base);m.reg_write(UC_X86_REG_EDX,owner)
            m.reg_write(UC_X86_REG_ECX,op);m.reg_write(UC_X86_REG_ESI,code);put(code+4,op)
            entry=img.u32(0x422ab8+4*img.read(0x422d70+op-300,1)[0])
            try:m.emu_start(entry,0x422a9b,count=100000)
            except Exception as error:raise RuntimeError(f'op {op}, case {n}, pc {m.reg_read(UC_X86_REG_EIP):x}, stack {bytes(m.mem_read(m.reg_read(UC_X86_REG_ESP),32)).hex()}') from error
            assert m.reg_read(UC_X86_REG_EIP)==0x422a9b
            commands.append(dict(op=op,n=n,initial=before,args=args[:],result=state()))
    timelines=[]
    for n in range(24):
        flags=(0,0x20000,0x4000000,0x4020000)[n%4];initial(n,flags)
        for k,offset in enumerate((0x88,0xcc)):
            floats(base+offset+0x18,(-1,0,.125,1.25,4,20)[n%6]+k*.25);floats(base+offset+0x1c,(-2.5,-.125,0,.5,1.57,2.75)[n%6]-k*.5)
        before=state();rate=(.5,1.,1.25)[n%3];floats(0x4a5788,rate);frames=[]
        for frame in range(40):
            put(base+0x4060,get(base+0x4060)|0x40000);put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,base)
            m.emu_start(0x41bb50,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end
            result=get(base+0x4060);status=m.reg_read(UC_X86_REG_EAX);frames.append(dict(result=state(),status=status))
            put(base+0x4060,result&~0x40000)
            if status:break
        timelines.append(dict(n=n,rate=rate,initial=before,frames=frames))
    # The per-frame side of the mode table 0x3df0, which the page reaches as soon as a command leaves
    # a record in mode 2 (+0x40 nibble). 0x41bb50 opens with the current-to-previous copy, then
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
        before=state();rate=(.5,1.,1.25)[n%3];floats(0x4a5788,rate);frames=[]
        for frame in range(40):
            put(base+0x4060,get(base+0x4060)|0x40000);put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,base)
            m.emu_start(0x41bb50,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end
            result=get(base+0x4060);status=m.reg_read(UC_X86_REG_EAX);frames.append(dict(result=state(),status=status))
            put(base+0x4060,result&~0x40000)
            if status:break
        row=dict(group=group,n=n,rate=rate,initial=before,flags=flags,
                 modes=[get(base+0x88+0x40),get(base+0xcc+0x40)],frames=frames)
        (mode_extra if group else mode_timelines).append(row)
    def interpolation():
        return [[get(base+offset+field) if field!=0x20 else int(bool(get(base+offset+0x24)&1)) for field in (0,4,8,12,0x14,0x18,0x1c,0x20,0x24,0x28,0x2c)] for offset in (0x3c8,0x3f8,0x428,0x458)]
    interpolations=[]
    for op in (405,407,429,431,441,443,445,447):
        for mirrored in (0,1):
            for mode in range(18):
                for variant in range(3):
                    n=mode*3+variant;initial(n,mirrored*0x80000)
                    duration=(0,7,35)[variant];rate=(.5,1.,1.25)[variant];floats(0x4a5788,rate)
                    before=state();args[:]=[duration,mode,f32((-999999.,-2.75,6.5)[mode%3]),f32((-999999.,-1.25,3.25)[mode%3])]
                    m.reg_write(UC_X86_REG_EBP,stack+0x2000);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,base);m.reg_write(UC_X86_REG_EDX,owner)
                    m.reg_write(UC_X86_REG_ECX,op);m.reg_write(UC_X86_REG_ESI,code);put(code+4,op)
                    m.emu_start(img.u32(0x422ab8+4*img.read(0x422d70+op-300,1)[0]),0x422a9b,count=100000);assert m.reg_read(UC_X86_REG_EIP)==0x422a9b
                    configured=interpolation();configured_state=state();frames=[]
                    for frame in range(40):
                        put(base+0x4060,get(base+0x4060)|0x40000);put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,base)
                        m.emu_start(0x41bb50,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end
                        status=m.reg_read(UC_X86_REG_EAX);frames.append(dict(result=state(),interpolation=interpolation(),status=status))
                        put(base+0x4060,get(base+0x4060)&~0x40000)
                        if status:break
                    interpolations.append(dict(op=op,n=n,rate=rate,initial=before,args=args[:],configured=configured,configuredState=configured_state,frames=frames))
    position_rows=[]
    def position_bands():
        return [[int(bool(get(base+off+0x4c)&1)) if field==0x48 else get(base+off+field)
                 for field in (*range(0xc,0x3c,4),0x3c,0x40,0x44,0x48,0x4c,0x50,0x60)]
                for off in (0x2f8,0x360)]
    for op in (401,403,425,426):
      for mode in range(18):
       for variant in range(9):
        n=mode*9+variant;initial(n,(0,0x80000,0x4000000)[variant%3]);rate=(.5,1,1.25)[variant%3]
        floats(0x4a5788,rate);before=state()
        args[:]=[(0,7,35)[variant//3],mode,f32((-999999.,-80.,24.5)[variant%3]),f32((100.,-999999.,72.125)[variant%3])]
        m.reg_write(UC_X86_REG_EBP,stack+0x2000);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,base);m.reg_write(UC_X86_REG_EDX,owner)
        m.reg_write(UC_X86_REG_ECX,op);m.reg_write(UC_X86_REG_ESI,code);put(code+4,op)
        if op in (425,426,427):args[:]=[(-1,0,35)[variant//3],f32(1.25),f32(-2.5),args[2],args[3],f32(-3.75),f32(.625)]
        m.emu_start(img.u32(0x422ab8+4*img.read(0x422d70+op-300,1)[0]),0x422a9b,count=100000);assert m.reg_read(UC_X86_REG_EIP)==0x422a9b
        configured=position_bands();configured_state=state();frames=[]
        for frame in range(76):
            put(base+0x4060,get(base+0x4060)|0x40000);put(stack,end)
            m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,base)
            m.emu_start(0x41bb50,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end
            status=m.reg_read(UC_X86_REG_EAX);frames.append(dict(result=state(),bands=position_bands(),status=status))
            put(base+0x4060,get(base+0x4060)&~0x40000)
            if status:break
        position_rows.append(dict(op=op,n=n,rate=rate,initial=before,args=args[:],configured=configured,configuredState=configured_state,frames=frames))
    directions=[]
    def direction_stop(machine,address,size,user):machine.emu_stop()
    for address in (0x41bf6b,0x41c0e1):m.hook_add(UC_HOOK_CODE,direction_stop,begin=address,end=address)
    for flags in (0,0x100000):
     for direction in (-2,-1,0,1,2):
      for velocity in (-10.,-.03,-.029999,0.,.029999,.03,10.,float('nan')):
       initial(0,flags);put(base+0x274,direction);floats(base+0x78,velocity);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,base)
       m.emu_start(0x41beee,0x422a9b,count=100)
       changed=m.reg_read(UC_X86_REG_EIP)==0x41bf6b
       directions.append(dict(flags=flags,direction=direction,velocityBits=f32(velocity),changed=changed,result=[m.reg_read(UC_X86_REG_ECX),m.reg_read(UC_X86_REG_ESI)] if changed else []))
    marks=[];vms=[0x70012000+k*0x800 for k in range(5)];nodes=[0x70017000+k*0x20 for k in range(4)]
    flag_options=(0,0x20,0x40,0x60,0x4000000,0x4000040,0xffffffff,0x12345678)
    for rootflags in flag_options:
     for selection in range(32):
      flags=[rootflags]+[flag_options[(selection+k*3)%8] for k in range(4)]
      for vm,flags2 in zip(vms,flags):m.mem_write(vm,bytes(0x700));put(vm+0x534,flags2)
      for node,index in zip(nodes,(1,2,3,4)):put(node,vms[index]);put(node+4,0)
      put(vms[0]+0x58c,nodes[0]);put(nodes[0]+4,nodes[1]);put(vms[1]+0x58c,nodes[2]);put(nodes[2]+4,nodes[3])
      put(stack,end);put(stack+4,vms[0]);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,owner)
      m.emu_start(0x46f220,end,count=1000);assert m.reg_read(UC_X86_REG_EIP)==end
      marks.append(dict(flags=flags,result=[get(vm+0x534) for vm in vms]))
    out=ROOT/"artifacts/th16/enemy-movement-native.json";out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),commands=commands,timelines=timelines,modeTimelines=mode_timelines,modeTimelinesExtra=mode_extra,interpolations=interpolations,positionRows=position_rows,directions=directions,marks=marks),separators=(",",":"))+"\n",encoding="utf-8")
    print(f"{len(commands)} setters, {len(interpolations)} scalar timelines, {len(position_rows)} position timelines")
if __name__=="__main__":main()
