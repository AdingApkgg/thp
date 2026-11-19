"""Camera setup 3bc10 and real look-at 56af0 against browser matrices.

Logical viewport sizes, direction vectors including degeneracy, and depth
offsets. Trigonometric library calls are supplied identically; GPU matrix
publication is observed. Compare complete view/projection float32 bytes and
the distance global, not final pixels.
"""
import hashlib,json,struct,subprocess,math
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    source='shared/th06nc/std-camera.mjs';before=hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
    script="""
import{createStdCamera}from'./shared/th06nc/std-camera.mjs';const cases=[],hex=a=>Buffer.from(a.buffer,a.byteOffset,a.byteLength).toString('hex');for(const [width,height]of [[384,448],[480,480],[1280,720]])for(const direction of [[0,0,1],[0,500,.8],[-100,25,1.2],[0,0,0],[1000,-1000,-1],[.1,.2,.001]])for(const depthOffset of [0,100,1000]){const r=createStdCamera({width,height,direction,depthOffset});cases.push({width,height,direction,depthOffset,view:hex(r.view),projection:hex(r.projection),distance:r.distance});}console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256()
    def hook(m,a,size,u):
        if a in [0x1402be095,0x1402be08f]:
            double=a==0x1402be08f;fmt='<d'if double else'<f';length=8 if double else 4;x=struct.unpack(fmt,m.reg_read(UC_X86_REG_XMM0).to_bytes(16,'little')[:length])[0];m.reg_write(UC_X86_REG_XMM0,int.from_bytes(struct.pack(fmt,math.tan(x)),'little'))
        elif a==0x14003a1e0:m.reg_write(UC_X86_REG_RAX,m.reg_read(UC_X86_REG_RCX))
        sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x1402be095,0x1402be08f,0x14003a1e0,0x1400977e0,0x140097680,0x1402bcf20]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    for index,c in enumerate(cases):
        m.mem_write(n.owner,bytes(0xe000));m.mem_write(n.owner+0xd40c,struct.pack('<3f',*c['direction']));m.mem_write(n.vm,struct.pack('<4I2f',32,16,c['width'],c['height'],0,1));sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.reg_write(UC_X86_REG_R8,n.vm);m.reg_write(UC_X86_REG_XMM1,int.from_bytes(struct.pack('<f',c['depthOffset']),'little'));m.emu_start(0x14003bc10,n.stack+0xf000,count=1000000)
        for name,base in [('view',0x140c21d18),('projection',0x140c21d58)]:
            actual=bytes(m.mem_read(base,64));wanted=bytes.fromhex(c[name]);assert actual==wanted,(index,name,list(struct.unpack('<16f',actual)),list(struct.unpack('<16f',wanted)));digest.update(actual)
        assert struct.unpack('<f',m.mem_read(n.owner+0xd274,4))[0]==c['distance'],(index,'distance')
    assert before==hashlib.sha256((ROOT/source).read_bytes()).hexdigest();report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256={source:before},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-std-camera-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
