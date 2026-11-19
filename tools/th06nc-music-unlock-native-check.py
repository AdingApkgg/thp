"""Actual music request 7bc80..7bcf4 unlock gates and MUSC mask.

The original scan wrapper calls actual Windows UCRT __stdio_common_vsscanf
through a controlled import, with the original format string verified. No cache, decoder, mixer, persistence
or full request lifecycle is claimed. Entire MUSC owner bytes compare.
"""
import ctypes,hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    source='shared/th06nc/music-unlock.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest();script="""
import{markMusicUnlocked}from'./shared/th06nc/music-unlock.mjs';const cases=[],hex=b=>Buffer.from(b).toString('hex'),paths=[null,'','data/bgm/th06_01.opus','data/bgm/th06_32','data/bgm/th06_33','data/bgm/th06_0','data/bgm/th06_-1','data/bgm/th06_+2suffix','data/bgm/th06_  3','data/bgm/th06_\\t4','data/bgm/th06_1e2','data/bgm/th06_0x10','data/bgm2/th06_01.opus','DATA/bgm/th06_01',' data/bgm/th06_01','data/bgm/th06_4294967297','data/bgm/th06_18446744073709551617','data/bgm/th06_\\0'+'1','data/bgm/th06_1\\0'+'2','data/bgm/th06_+','data/bgm/th06_\\n-4294967295'];for(const path of paths)for(const ownerState of [0,8,9,10])for(const blocked of [false,true])for(const mask of [0,0x55555555,0xffffffff]){const before=Uint8Array.from({length:16},(_,i)=>i*17);new DataView(before.buffer).setUint32(12,mask,true);const after=before.slice();markMusicUnlocked(after,{ownerState,blocked,path});cases.push({path,ownerState,blocked,before:hex(before),after:hex(after)});}console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256();crt=ctypes.CDLL('ucrtbase');scan=crt.__stdio_common_vsscanf;scan.restype=ctypes.c_int;scan.argtypes=[ctypes.c_uint64,ctypes.c_char_p,ctypes.c_size_t,ctypes.c_char_p,ctypes.c_void_p,ctypes.c_void_p]
    assert bytes(m.mem_read(0x14030aa40,18)).split(b'\0')[0]==b'data/bgm/th06_%d'
    def cstring(p):return bytes(m.mem_read(p,512)).split(b'\0')[0]
    def scan_hook(m,a,size,u):
        sp=m.reg_read(UC_X86_REG_RSP);va=struct.unpack('<Q',m.mem_read(sp+0x30,8))[0];dst=struct.unpack('<Q',m.mem_read(va,8))[0];result=ctypes.c_int(0);hostva=ctypes.c_void_p(ctypes.addressof(result));count=scan(m.reg_read(UC_X86_REG_RCX),cstring(m.reg_read(UC_X86_REG_RDX)),m.reg_read(UC_X86_REG_R8),cstring(m.reg_read(UC_X86_REG_R9)),None,ctypes.byref(hostva));m.mem_write(dst,struct.pack('<i',result.value));m.reg_write(UC_X86_REG_EAX,count&0xffffffff);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    m.mem_write(0x1402c0558,struct.pack('<Q',n.vm+0x9000));m.hook_add(UC_HOOK_CODE,scan_hook,begin=n.vm+0x9000,end=n.vm+0x9000)
    for i,c in enumerate(cases):
        m.mem_write(n.owner+0x42c,struct.pack('<i',c['ownerState']));m.mem_write(0x1404f278c,bytes([int(c['blocked'])]));m.mem_write(0x1404ff154,bytes.fromhex(c['before']));m.mem_write(n.assets,bytes(1024));
        if c['path']is not None:m.mem_write(n.assets,c['path'].encode()+b'\0')
        m.reg_write(UC_X86_REG_RCX,n.owner);m.reg_write(UC_X86_REG_RDX,n.assets if c['path']is not None else 0);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x14007bc80,0x14007bcf4,count=1000);assert m.reg_read(UC_X86_REG_RIP)==0x14007bcf4,(i,'stop');actual=bytes(m.mem_read(0x1404ff154,16));assert actual==bytes.fromhex(c['after']),(i,c['path'],'MUSC');digest.update(actual)
    assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha
    report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-music-unlock-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'cases':len(cases)}))
if __name__=='__main__':main()

