"""Original ending @ dispatch and trailing line advance, 2be75 branches.

Full owner/cursor and ordered requests compare for every command occurrence in
seven scripts plus synthetic boundaries. Numeric helper uses real original code
and UCRT atoi. ANM/background/music/script-switch services are controlled, not
original rendering/cache/loader implementations. Outer update/text/lifecycle and
browser excluded. Script-switch stub rewinds the same fixture memory explicitly.
"""
import ctypes,hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/ending-command.mjs','shared/th06nc/ending-stream.mjs'];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources};script="""
import{readFileSync,readdirSync}from'node:fs';import{applyEndingCommand}from'./shared/th06nc/ending-command.mjs';const cases=[],hex=b=>Buffer.from(b).toString('hex'),add=(script,offset,fail,file,override=null)=>{const bytes=Uint8Array.from({length:0x1280},(_,j)=>(j*17+cases.length)&255),v=new DataView(bytes.buffer);v.setBigUint64(0x1250,BigInt(offset),true);const before=hex(bytes),cleared=override??Uint8Array.from({length:96},(_,j)=>[0,1,98,99,100,255][(j+cases.length)%6]),events=[],state={bytes,script},services={loadBackground:path=>{events.push({kind:'background',path});return fail?-1:0;},bindAnm:(offset,id)=>events.push({kind:'anm',offset,id}),bindSprite:(offset,id)=>events.push({kind:'sprite',offset,id}),playMusic:path=>events.push({kind:'music',path}),fadeMusic:value=>events.push({kind:'fade',value}),switchScript:path=>{events.push({kind:'script',path});if(!fail)v.setBigUint64(0x1250,0n,true);return fail?-1:0;},cleared},action=applyEndingCommand(state,services);cases.push({script:hex(script),offset,fail,file,before,cleared:hex(cleared),after:hex(bytes),events,action});};const home='runtimes/th06nc/artifacts/scripts/th06ED.dat',files=readdirSync(home).filter(n=>n.endsWith('.end'));for(const file of files){const raw=readFileSync(home+'/'+file),script=new Uint8Array([...raw,0,10,64,122,10,120]);for(let p=0;p+1<raw.length;p++)if(raw[p]===64&&(p===0||[10,13].includes(raw[p-1])))for(const fail of [false,true])add(script,p,fail,file);}
for(const command of ['0','1','2','3','V','v','M','s','c','r','w'])for(const value of ['0','-1','2147483647','2147483648']){const script=new TextEncoder().encode('@'+command+value+'\\0'+'0\\0'+'\\r\\n@z\\nX');add(script,0,false,null);}for(let index=-1;index<34;index++){const cleared=new Uint8Array(96);if(index>=0&&index<32){const profile=Math.floor(index/8),field=index%8;cleared[profile*24+(field<4?12+field:17+field-4)]=99;}if(index>=32)cleared[index===32?16:21]=99;for(const fail of [false,true])add(new TextEncoder().encode('@Fdata/staff00.end\\0\\n@z\\nX'),0,fail,null,cleared);}console.log(JSON.stringify({files,cases}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;events=[];digest=hashlib.sha256();atoi=ctypes.CDLL('ucrtbase').atoi;atoi.argtypes=[ctypes.c_char_p];atoi.restype=ctypes.c_int;failure=False
    for name in data['files']:
        p='runtimes/th06nc/artifacts/scripts/th06ED.dat/'+name;hashes[p]=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
    def text_at(p):return bytes(m.mem_read(p,4096)).split(b'\0')[0].decode()
    def hook(m,a,size,u):
        sp=m.reg_read(UC_X86_REG_RSP)
        if a==n.vm+0x9000:m.reg_write(UC_X86_REG_EAX,atoi(bytes(m.mem_read(m.reg_read(UC_X86_REG_RCX),4096)).split(b'\0')[0])&0xffffffff)
        elif a==0x140007620:events.append(dict(kind='background',path=text_at(m.reg_read(UC_X86_REG_R8))));m.reg_write(UC_X86_REG_EAX,0xffffffff if failure else 0)
        elif a in [0x140002760,0x140002980]:events.append(dict(kind='anm'if a==0x140002760 else'sprite',offset=m.reg_read(UC_X86_REG_RDX)-n.owner,id=m.reg_read(UC_X86_REG_R8)&0xffffffff))
        elif a==0x14007bc80:events.append(dict(kind='music',path=text_at(m.reg_read(UC_X86_REG_RDX))))
        elif a==0x14007c000:events.append(dict(kind='fade',value=struct.unpack('<f',struct.pack('<I',m.reg_read(UC_X86_REG_XMM1)&0xffffffff))[0]))
        elif a==0x14002b7a0:
            events.append(dict(kind='script',path=text_at(m.reg_read(UC_X86_REG_RDX))))
            if not failure:m.mem_write(n.owner+0x1250,struct.pack('<Q',n.assets))
            m.reg_write(UC_X86_REG_EAX,0xffffffff if failure else 0)
        m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    m.mem_write(0x1402c0328,struct.pack('<Q',n.vm+0x9000))
    for a in [n.vm+0x9000,0x140007620,0x140002760,0x140002980,0x14007bc80,0x14007c000,0x14002b7a0]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    stops={0x14002be60:'continue',0x14002bbcc:'yield',0x14002c52d:'end'}
    def stop(m,a,size,u):m.emu_stop()
    for a in stops:m.hook_add(UC_HOOK_CODE,stop,begin=a,end=a)
    for i,c in enumerate(data['cases']):
        raw=bytes.fromhex(c['script']);initial=bytearray.fromhex(c['before']);struct.pack_into('<Q',initial,0x1250,n.assets+c['offset']);m.mem_write(n.assets,raw);m.mem_write(n.owner,bytes(initial));m.mem_write(0x1404ff0f4,bytes.fromhex(c['cleared']));failure=c['fail'];events.clear()
        for reg,value in [(UC_X86_REG_R14,n.owner),(UC_X86_REG_RDX,n.assets+c['offset']),(UC_X86_REG_RSI,0x140000000),(UC_X86_REG_R10,0),(UC_X86_REG_R12,0),(UC_X86_REG_R15,0),(UC_X86_REG_RSP,n.stack+0x8000)]:m.reg_write(reg,value)
        m.emu_start(0x14002be75,0,count=100000);pc=m.reg_read(UC_X86_REG_RIP);assert pc in stops,(i,'stop',hex(pc));actual=bytearray(m.mem_read(n.owner,0x1280));ptr=struct.unpack_from('<Q',actual,0x1250)[0];struct.pack_into('<Q',actual,0x1250,ptr-n.assets)
        assert actual==bytes.fromhex(c['after']),(i,c['file'],'owner',[(hex(p),a,b)for p,(a,b)in enumerate(zip(actual,bytes.fromhex(c['after'])))if a!=b][:8]);assert events==c['events'],(i,'events',events,c['events']);assert stops[pc]==c['action'],(i,'action');digest.update(actual);digest.update(json.dumps(events).encode())
    assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in hashes}
    report=dict(scope=__doc__,cases=len(data['cases']),originalScripts=len(data['files']),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-ending-command-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'cases':len(data['cases'])}))
if __name__=='__main__':main()
