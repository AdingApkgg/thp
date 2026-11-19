"""Actual full 2c600 ending draw callback: owner and ordered draw requests.

Texture query, background blit, VM draw and fade quad are controlled transports.
No native GPU/glyph/texture pixels are claimed. Includes alternate selection,
source-height threshold, float-to-int edges, all fade modes and display clocks.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    source='shared/th06nc/ending-draw.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest();script="""
import{drawEnding}from'./shared/th06nc/ending-draw.mjs';const cases=[],hex=b=>Buffer.from(b).toString('hex');for(let mode=0;mode<=5;mode++)for(const duration of [0,1,30,2147483647])for(const clock of [0,1,29,30,16777216])for(const handles of [[-1,-1,false],[3,-1,true],[-1,4,false],[-1,4,true],[3,4,false],[3,4,true]]){const index=cases.length,bytes=Uint8Array.from({length:0x1280},(_,j)=>(j*17+index)&255),v=new DataView(bytes.buffer);v.setInt32(0,clock,true);v.setInt32(4,duration,true);v.setInt32(0x30,mode,true);v.setFloat32(0x1240,[0,12.9,-3.9,NaN,Infinity][index%5],true);v.setFloat32(0x1244,[0,37.5,-999,Infinity,-Infinity][index%5],true);for(let i=0;i<16;i++)v.setUint16(0x70+i*288,(index+i)%3?0x737:0,true);const before=hex(bytes),viewport=[{x:0,y:0,width:854,height:480},{x:15,y:-20,width:1280,height:960},{x:0,y:0,width:640,height:360}][index%3],environment={primary:handles[0],alternate:handles[1],useAlternate:handles[2],viewport},dimensions={width:[1920,1921,3840][index%3],height:2160},events=[],result=drawEnding(bytes,environment,{textureSize:handle=>{events.push({kind:'size',handle});return dimensions;},drawBackground:r=>events.push({kind:'background',...r}),drawVm:(offset,args)=>events.push({kind:'vm',offset,args}),drawFade:r=>events.push({kind:'fade',...r})});cases.push({before,after:hex(bytes),environment,dimensions,events,result});}console.log(JSON.stringify(cases));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;events=[];digest=hashlib.sha256();dimensions={}
    def hook(m,a,size,u):
        sp=m.reg_read(UC_X86_REG_RSP)
        if a==0x140083f00:
            events.append(dict(kind='size',handle=m.reg_read(UC_X86_REG_ECX)));m.mem_write(m.reg_read(UC_X86_REG_RDX),struct.pack('<i',dimensions['width']));m.mem_write(m.reg_read(UC_X86_REG_R8),struct.pack('<i',dimensions['height']))
        elif a==0x1400828b0:
            stack=tuple(struct.unpack('<i',m.mem_read(sp+0x28+j*8,4))[0]for j in range(6));signed=lambda x:struct.unpack('<i',struct.pack('<I',x&0xffffffff))[0];events.append(dict(kind='background',left=signed(m.reg_read(UC_X86_REG_RCX)),top=signed(m.reg_read(UC_X86_REG_RDX)),right=signed(m.reg_read(UC_X86_REG_R8)),bottom=signed(m.reg_read(UC_X86_REG_R9)),source=list(stack[:4]),handle=stack[4],transparent=stack[5]))
        elif a==0x140002a80:events.append(dict(kind='vm',offset=m.reg_read(UC_X86_REG_RDX)-n.owner,args=[m.reg_read(UC_X86_REG_R8)&0xffffffff,m.reg_read(UC_X86_REG_R9)&255,bytes(m.mem_read(sp+0x28,1))[0]]))
        elif a==0x140075be0:
            x,y,width,height=struct.unpack('<4f',m.mem_read(m.reg_read(UC_X86_REG_RCX),16));events.append(dict(kind='fade',rect=[x,y,width,height],color=m.reg_read(UC_X86_REG_RDX)&0xffffffff))
        m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x140083f00,0x1400828b0,0x140002a80,0x140075be0,0x1402bcf20]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    m.mem_write(0x140a6e9b0,struct.pack('<Q',n.manager))
    for i,c in enumerate(data):
        e=c['environment'];dimensions=c['dimensions'];m.mem_write(n.owner,bytes.fromhex(c['before']));m.mem_write(n.manager+0x22f90,struct.pack('<2i',e['primary'],e['alternate']));m.mem_write(0x140c21d14,bytes([e['useAlternate']]));vp=e['viewport'];m.mem_write(0x140c21e3c,struct.pack('<4i',vp['x'],vp['y'],vp['width'],vp['height']));sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);events.clear();m.emu_start(0x14002c600,n.stack+0xf000,count=10000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000,(i,'stop');actual=bytes(m.mem_read(n.owner,0x1280));assert actual==bytes.fromhex(c['after']),(i,'owner');assert events==c['events'],(i,'requests',events,c['events']);assert m.reg_read(UC_X86_REG_EAX)==c['result'];digest.update(actual)
    assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha
    report=dict(scope=__doc__,cases=len(data),stateSha256=digest.hexdigest(),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-ending-draw-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'cases':len(data)}))
if __name__=='__main__':main()
