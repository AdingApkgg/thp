"""Summary result draw 72890, real ANMs and native formatted ASCII queue.

Whole result/ASCII owners, ordered draw VMs/camera and native UCRT output.
Two logical rank-head pointers and resource addresses are normalized.
GPU, state dispatch, other result pages and standalone supervisor tail excluded.
"""
import ctypes,hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/'+s+'.mjs'for s in ['result-summary-draw','result-state','score-name-input','score-tables','ascii-text','score-popup-draw','anm-bank','anm-rebind','anm-vm']];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources};script="""
import{readFileSync}from'node:fs';import{createHash}from'node:crypto';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{ResultState,resultAssets,resultTextAsset}from'./shared/th06nc/result-state.mjs';import{createAsciiTextState}from'./shared/th06nc/ascii-text.mjs';import{createDefaultScoreTables}from'./shared/th06nc/score-tables.mjs';import{drawResultSummary}from'./shared/th06nc/result-summary-draw.mjs';const refs=[...resultAssets,resultTextAsset,{archive:'th06IN.dat',file:'ascii.anm',slot:1,base:0}],bank=new AnmBank(),sha=b=>createHash('sha256').update(b).digest('hex'),hex=b=>Buffer.from(b).toString('hex');for(const r of refs)bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+r.archive+'/'+r.file)),r.base,{slot:r.slot});const tables=createDefaultScoreTables();for(const side of [0,1]){let t=tables.get(`0/1/${side}`);for(let i=0;i<10;i++){t[i][23]=[1,6,7,99][i%4];if(i===2){t[i][9]=1;new DataView(t[i].buffer).setBigUint64(12,0xffffffffffffffffn,true);}}}const scenes=[];
for(const kind of [15,16])for(const index of [0,1,2,3])for(const baseX of [160,640])for(const cursor of [0,250,256])for(const variant of [0,1,2,3,4,5]){for(const side of [0,1])tables.set(`${index>>1}/1/${(index%2)*2+side}`,tables.get(`0/1/${side}`));const state=new ResultState(bank),a=state.v;a.setInt32(0x9e94,kind,true);a.setInt32(0x9e9c,9,true);a.setInt32(0xa8,1,true);a.setInt32(4,index,true);[baseX,48,.25].forEach((x,i)=>a.setFloat32(0x1138+i*4,x,true));[40,25,.5].forEach((x,i)=>a.setFloat32(0x2b18+i*4,x,true));a.setUint32(0x2b3c,variant&1?0x80ffccaa:0xffffffff,true);[2.5,-3.5,.5].forEach((x,i)=>a.setFloat32(0xb0+i*4+0x18,x,true));const environment={score:'18446744073709551615',difficulty:[0,1,4,1,4,0][variant],lifeProtection:Boolean(variant&1),messageClock:[0,89500,39600,12345,123456,-1][variant],cleared:Boolean(variant&2),continuesUsed:variant,deathCount:variant-1,bombCount:variant*3,captures:variant*2,timingNumerator:[0,1,.5,2,0,1.125][variant],timingDenominator:variant===4?0:1},ascii=createAsciiTextState(bank);ascii.v.setInt32(0x7bb0,cursor,true);const calls=[];drawResultSummary(state,(vm,r)=>calls.push({kind:'draw',offset:r.offset,path:r.path,state:hex(vm.state)}),{ascii,tables,environment,setupCamera:r=>calls.push({kind:'camera',...r})});scenes.push({kind,index,baseX,cursor,variant,environment,ownerSha256:sha(state.bytes),fontSha256:sha(ascii.bytes),calls});}console.log(JSON.stringify({refs,tables:[tables.get('0/1/0').map(hex),tables.get('0/1/1').map(hex)],scenes}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;n.load_title(data['refs']);fontBase=0x1403de620;shim=n.vm+0x9000;m.mem_write(shim,b'\xc3');m.mem_write(0x1402c0528,struct.pack('<Q',shim));crt=ctypes.CDLL('ucrtbase');formatter=crt.__stdio_common_vsprintf;formatter.restype=ctypes.c_int;formatter.argtypes=[ctypes.c_uint64,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_char_p,ctypes.c_void_p,ctypes.c_void_p];calls=[];digest=hashlib.sha256()
    offsets=[0xb0+i*288 for i in range(38)]+[0x2b70+i*288 for i in range(16)]+[0x3d70+i*288 for i in range(5)]+[0x4310]
    def normal_vm(raw):
        raw=bytearray(raw)
        for field in [0xf0,0xf8]:
            ptr=struct.unpack_from('<Q',raw,field)[0]
            if ptr:struct.pack_into('<Q',raw,field,ptr-next(lo for lo,hi in n.ranges if lo<=ptr<hi))
        ptr=struct.unpack_from('<Q',raw,0x100)[0]
        if ptr:struct.pack_into('<Q',raw,0x100,(ptr-n.manager-0x608)//64+1)
        return raw
    def normalized_owner():
        raw=bytearray(m.mem_read(n.owner,0xbb48))
        for offset in offsets:raw[offset:offset+288]=normal_vm(raw[offset:offset+288])
        raw[0x4458:0x49f8]=bytes(0x5a0)
        return raw
    def hook(m,a,size,u):
        sp=m.reg_read(UC_X86_REG_RSP)
        if a==0x1402bdee2:m.mem_write(m.reg_read(UC_X86_REG_RCX),bytes([m.reg_read(UC_X86_REG_RDX)&255])*m.reg_read(UC_X86_REG_R8))
        elif a==shim:
            fmt=bytes(m.mem_read(m.reg_read(UC_X86_REG_R9),100)).split(b'\0')[0];assert fmt in [b'%2d',b'%8s',b'%8s %9llu(%d)',b'%8s %9llu(1)',b'%8s %9llu(C)',b'%llu',b'%d',b'100%%',b'%3.2f%%'] or(len(fmt)==8 and set(fmt)<=set(b' _')),fmt;va=struct.unpack('<Q',m.mem_read(sp+0x30,8))[0];args=list(struct.unpack('<3Q',m.mem_read(va,24)));buffers=[]
            if b'%8s'in fmt:
                raw=bytes(m.mem_read(args[0],100)).split(b'\0')[0];buffers.append(ctypes.create_string_buffer(raw));args[0]=ctypes.addressof(buffers[-1])
            argument=(ctypes.c_uint64*3)(*args);out=ctypes.create_string_buffer(512);length=formatter(m.reg_read(UC_X86_REG_RCX),out,512,fmt,None,argument);assert length>=0;m.mem_write(m.reg_read(UC_X86_REG_RDX),out.value+b'\0');m.reg_write(UC_X86_REG_RAX,length)
        elif a in [0x140002a80,0x1400036c0]:
            ptr=m.reg_read(UC_X86_REG_RDX);calls.append(dict(kind='draw',offset=ptr-n.owner,path='flat'if a==0x140002a80 else'rotated',state=normal_vm(bytes(m.mem_read(ptr,288))).hex()))
        elif a==0x14007b120:calls.append(dict(kind='camera',minZ=struct.unpack('<f',struct.pack('<I',m.reg_read(UC_X86_REG_XMM1)&0xffffffff))[0],maxZ=struct.unpack('<f',struct.pack('<I',m.reg_read(UC_X86_REG_XMM2)&0xffffffff))[0]))
        m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x1402bdee2,0x1402bcf20,shim,0x140002a80,0x1400036c0,0x14007b120]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    def run(address,rcx):
        sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,rcx);m.emu_start(address,n.stack+0xf000,count=2000000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000
    m.mem_write(n.owner,bytes(0xbb48));m.mem_write(n.owner+0x9e7c,struct.pack('<i',1));m.reg_write(UC_X86_REG_RDI,0x7d0);m.reg_write(UC_X86_REG_RBX,n.owner+0x3d70);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x14007583c,0x140075a34,count=1000000);m.reg_write(UC_X86_REG_R15,n.owner);m.reg_write(UC_X86_REG_R13,0);m.reg_write(UC_X86_REG_R12D,0x798);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x140073e93,0x140073ff3,count=1000000);baseline=bytes(m.mem_read(n.owner,0xbb48))
    for index,s in enumerate(data['scenes']):
        m.mem_write(n.owner,baseline);m.mem_write(n.owner+0x9e94,struct.pack('<i',s['kind']));m.mem_write(n.owner+0x9e9c,struct.pack('<i',9));m.mem_write(n.owner+0xa8,struct.pack('<i',1));m.mem_write(n.owner+4,struct.pack('<i',s['index']));m.mem_write(n.owner+0x1138,struct.pack('<3f',s['baseX'],48,.25));m.mem_write(n.owner+0x2b18,struct.pack('<3f',40,25,.5));m.mem_write(n.owner+0x2b3c,struct.pack('<I',0x80ffccaa if s['variant']&1 else 0xffffffff));m.mem_write(n.owner+0xb0+0x18,struct.pack('<3f',2.5,-3.5,.5));e=s['environment']
        for key,address,fmt in [('score',0x4f2798,'Q'),('difficulty',0x4f27c0,'i'),('lifeProtection',0x4f27c4,'B'),('messageClock',0x4ff0d8,'i'),('cleared',0x4f27b3,'B'),('continuesUsed',0x4ff0dc,'B'),('deathCount',0x4f1e60,'i'),('bombCount',0x4f1e64,'i'),('captures',0x4f1e68,'i'),('timingNumerator',0xc21d0c,'f'),('timingDenominator',0xc21d10,'f')]:m.mem_write(0x140000000+address,struct.pack('<'+fmt,int(e[key])if fmt!='f'else e[key]))
        for side in range(2):
            first=n.vm+0x2000+side*0x400;m.mem_write(n.owner+0x4458+((s['index']//2)*20+4+(s['index']%2)*2+side)*24+16,struct.pack('<Q',first))
            for row,record in enumerate(data['tables'][side]):
                ptr=n.assets+0x180000+side*0x400+row*64;m.mem_write(ptr,bytes.fromhex(record));m.mem_write(first+row*32,struct.pack('<3Q',ptr,0,first+(row+1)*32 if row<9 else 0))
        m.mem_write(fontBase,bytes(0xdbb8));run(0x140009790,fontBase);m.mem_write(fontBase+0x7bb0,struct.pack('<i',s['cursor']));calls.clear();run(0x140072890,n.owner);actual=normalized_owner();assert hashlib.sha256(actual).hexdigest()==s['ownerSha256'],(index,'owner');assert calls==s['calls'],(index,'draw',len(calls),len(s['calls']),next((i for i,(a,b)in enumerate(zip(calls,s['calls']))if a!=b),None));font=bytearray(m.mem_read(fontBase,0xdbb8))
        for p in [0x10,0x130]:font[p:p+288]=normal_vm(font[p:p+288])
        assert hashlib.sha256(font).hexdigest()==s['fontSha256'],(index,'font',struct.unpack_from('<i',font,0x7bb0)[0]);digest.update(actual);digest.update(font)
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items());report=dict(scope=__doc__,scenes=len(data['scenes']),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-result-summary-draw-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
