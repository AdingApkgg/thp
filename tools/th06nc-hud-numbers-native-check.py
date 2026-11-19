"""Ordinary HUD numeric requests and refresh counters, 413c0..415b2.

Actual native code and Windows CRT %.9llu/%d formatting; glyph/cache drawing
has its own check. GPU pixels, high-score persistence and other HUD excluded.
"""
import ctypes,hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    source='shared/th06nc/hud-numbers.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
    script="""
import{drawHudNumbers}from'./shared/th06nc/hud-numbers.mjs';const scenes=[];let index=0;for(const displayScore of [0n,1n,999999999n,1000000000n,9999999990n])for(const highScore of [1000000n,1000000000n,9999999990n])for(const inputFlags of [0,0x155,0x2aa,0x3ff,0xbeef,0xffffffff])for(const force of [false,true]){const totalGraze=[0,1,-1,2147483647][index%4],pointStageCount=[0,65535,65536,-1][index%4],calls=[],flags=drawHudNumbers(r=>calls.push(r),{displayScore,highScore,totalGraze,pointStageCount,pointTotalCount:(pointStageCount+19)&65535,inputFlags,force});scenes.push({displayScore:String(displayScore),highScore:String(highScore),totalGraze,pointStageCount,inputFlags,force,calls,flags});index++;}console.log(JSON.stringify(scenes));
"""
    scenes=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;calls=[];digest=hashlib.sha256();crt=ctypes.CDLL('ucrtbase');formatter=crt.__stdio_common_vsprintf;formatter.restype=ctypes.c_int;formatter.argtypes=[ctypes.c_uint64,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_char_p,ctypes.c_void_p,ctypes.c_void_p]
    def hook(m,a,size,u):
        sp=m.reg_read(UC_X86_REG_RSP);ptr=m.reg_read(UC_X86_REG_R8);fmt=bytes(m.mem_read(ptr,16)).split(b'\0')[0].decode();value=m.reg_read(UC_X86_REG_R9)
        if fmt=='%d':value=(value&0xffffffff)-(0x100000000 if value&0x80000000 else 0)
        else:assert fmt=='%.9llu'
        out=ctypes.create_string_buffer(80);argument=ctypes.c_uint64(value&0xffffffffffffffff);assert formatter(1,out,80,fmt.encode(),None,ctypes.byref(argument))>0;calls.append(dict(format=fmt,value=str(value),text=out.value.decode(),position=list(struct.unpack('<3f',m.mem_read(m.reg_read(UC_X86_REG_RDX),12)))));m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    m.hook_add(UC_HOOK_CODE,hook,begin=0x140009aa0,end=0x140009aa0)
    for index,s in enumerate(scenes):
        m.mem_write(n.vm,bytes(0x10000));m.mem_write(n.vm+0x48,struct.pack('<I',s['inputFlags']));m.mem_write(0x1404f2790,struct.pack('<Q',int(s['displayScore'])));m.mem_write(0x1404f27a8,struct.pack('<Q',int(s['highScore'])));m.mem_write(0x1404ff0cc,struct.pack('<i',s['totalGraze']));m.mem_write(0x1404f27ba,struct.pack('<H',s['pointStageCount']&65535));m.mem_write(0x140c21dc0,bytes([0x10 if s['force'] else 0]));m.reg_write(UC_X86_REG_RBX,n.vm);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.reg_write(UC_X86_REG_XMM7,struct.unpack('<I',struct.pack('<f',723))[0]);m.reg_write(UC_X86_REG_XMM9,0);calls.clear();m.emu_start(0x1400413c0,0x1400415b2,count=1000000);assert calls==s['calls'],(index,calls,s['calls']);assert struct.unpack('<I',m.mem_read(n.vm+0x48,4))[0]==s['flags'],(index,'flags');digest.update(json.dumps(calls).encode())
    assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha;report=dict(scope=__doc__,scenes=len(scenes),drawRequests=sum(len(s['calls'])for s in scenes),stateSha256=digest.hexdigest(),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-hud-numbers-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()

