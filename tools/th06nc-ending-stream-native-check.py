"""Actual ending integer helper 2b6e0 through actual Windows UCRT atoi.

Return value, complete owner with cursor update and untouched script bytes
compare for synthetic edge tokens and NUL-delimited positions in all seven
original ending/Staff scripts. Appended sentinels make the accepted memory span
explicit. Full command dispatch, script scheduling, rendering/browser excluded.
"""
import ctypes,hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    source='shared/th06nc/ending-stream.mjs';hashes={source:hashlib.sha256((ROOT/source).read_bytes()).hexdigest()};script="""
import{readFileSync,readdirSync}from'node:fs';import{readEndingInteger}from'./shared/th06nc/ending-stream.mjs';const cases=[],hex=b=>Buffer.from(b).toString('hex');for(const text of ['','0','1','-1','+2suffix','  42','\\t-19','word','2147483647','2147483648','-2147483649','4294967297','18446744073709551617','+','12e3','0x10'])for(const zeros of [1,2,5]){const bytes=new Uint8Array([...new TextEncoder().encode(text),...new Uint8Array(zeros),10,255]);cases.push({bytes:hex(bytes),offset:0,...readEndingInteger(bytes,0)});}const home='runtimes/th06nc/artifacts/scripts/th06ED.dat',files=readdirSync(home).filter(n=>n.endsWith('.end'));for(const name of files){const raw=readFileSync(home+'/'+name),bytes=new Uint8Array([...raw,0,0,10,255]);for(let p=0;p<raw.length;p++){if(p===0||raw[p-1]===0){cases.push({file:name,bytes:hex(bytes),offset:p,...readEndingInteger(bytes,p)});}if(raw[p]===64&&p+2<raw.length)cases.push({file:name,bytes:hex(bytes),offset:p+2,...readEndingInteger(bytes,p+2)});}}console.log(JSON.stringify({files,cases}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256();atoi=ctypes.CDLL('ucrtbase').atoi;atoi.argtypes=[ctypes.c_char_p];atoi.restype=ctypes.c_int
    for name in data['files']:
        path='runtimes/th06nc/artifacts/scripts/th06ED.dat/'+name;hashes[path]=hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
    def hook(m,a,size,u):
        p=m.reg_read(UC_X86_REG_RCX);raw=bytes(m.mem_read(p,4096)).split(b'\0')[0];m.reg_write(UC_X86_REG_EAX,atoi(raw)&0xffffffff);sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    m.mem_write(0x1402c0328,struct.pack('<Q',n.vm+0x9000));m.hook_add(UC_HOOK_CODE,hook,begin=n.vm+0x9000,end=n.vm+0x9000)
    for i,c in enumerate(data['cases']):
        raw=bytes.fromhex(c['bytes']);initial=bytearray((j*17+i)&255 for j in range(0x1280));struct.pack_into('<Q',initial,0x1250,n.assets+c['offset']);m.mem_write(n.assets,raw);m.mem_write(n.owner,bytes(initial));sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.emu_start(0x14002b6e0,n.stack+0xf000,count=10000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000,(i,'stop');value=ctypes.c_int(m.reg_read(UC_X86_REG_EAX)).value;assert value==c['value'],(i,'value');struct.pack_into('<Q',initial,0x1250,n.assets+c['next']);actual=bytes(m.mem_read(n.owner,0x1280));assert actual==initial,(i,'owner');assert bytes(m.mem_read(n.assets,len(raw)))==raw,(i,'script mutation');digest.update(actual)
    assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in hashes}
    report=dict(scope=__doc__,cases=len(data['cases']),originalScripts=len(data['files']),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-ending-stream-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'cases':len(data['cases']),'scripts':len(data['files'])}))
if __name__=='__main__':main()
