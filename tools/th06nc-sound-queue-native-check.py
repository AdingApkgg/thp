"""Compare the three-slot audio consumer and all sound IDs with native 76a30.

DxLib volume/play calls are observed boundaries; decoded waveforms and mixing
are separate tests. Includes muted queues, missing handles and interior holes.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    source='shared/th06nc/sound-queue.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
    script="""
import{consumeSoundQueue,soundDefinitions}from'./shared/th06nc/sound-queue.mjs';
const cases=[];for(let id=0;id<34;id++)for(const volume of [0,1,5,10,255])for(const missing of [false,true])for(const initial of [[id,-1,7],[id,7,10],[-1,id,10]]){const slots=[...initial],handles=soundDefinitions.map((_,i)=>missing&&i===id?-1:100+i),events=[];consumeSoundQueue(slots,{volume,handles,setVolume:r=>events.push({kind:'volume',...r}),playSound:r=>events.push({kind:'play',...r})});cases.push({id,volume,initial,slots,handles,events});}console.log(JSON.stringify({cases,definitions:soundDefinitions}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;events=[];digest=hashlib.sha256()
    for i,d in enumerate(data['definitions']):
        sourceIndex,attenuation,pad=struct.unpack('<ihh',m.mem_read(0x1403de430+i*8,8));ptr=struct.unpack('<Q',m.mem_read(0x1403091a0+sourceIndex*8,8))[0];file=bytes(m.mem_read(ptr,80)).split(b'\0')[0].decode().split('/')[-1];assert (sourceIndex,attenuation,file)==(d['source'],d['attenuation'],d['file'])
    def hook(m,a,size,u):
        ecx=m.reg_read(UC_X86_REG_ECX);edx=m.reg_read(UC_X86_REG_EDX)
        if a==0x1400ca7d0:events.append(dict(kind='volume',handle=edx,value=ecx))
        else:events.append(dict(kind='play',handle=ecx,mode=edx,restart=m.reg_read(UC_X86_REG_R8D)))
        sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x1400ca7d0,0x1400c8110]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    for i,c in enumerate(data['cases']):
        m.mem_write(0x140509670,struct.pack('<3i',*c['initial']));m.mem_write(0x140509898,struct.pack('<34i',*c['handles']));m.mem_write(0x140c21db7,bytes([c['volume']]));sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.assets));m.reg_write(UC_X86_REG_RSP,sp);events.clear();m.emu_start(0x140076a30,n.assets,count=10000);assert m.reg_read(UC_X86_REG_RIP)==n.assets
        actual=bytes(m.mem_read(0x140509670,12));assert list(struct.unpack('<3i',actual))==c['slots'],(i,'queue');assert events==c['events'],(i,events,c['events']);digest.update(actual)
    assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha
    report=dict(scope=__doc__,cases=len(data['cases']),stateSha256=digest.hexdigest(),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-sound-queue-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
