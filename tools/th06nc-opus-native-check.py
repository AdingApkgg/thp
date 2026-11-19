"""Original 7ea60 header loader and 7ec80 packet reader, all 36 BGM files.

File callbacks, allocation and Opus decoder calls are observed/stubbed service
boundaries. Compares header fields and every decoder packet byte; excludes
the Opus decoder waveform, Ogg framing and platform mixing equivalence.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    source='shared/th06nc/opus-container.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
    script="""
import{readFileSync,readdirSync}from'node:fs';import{createHash}from'node:crypto';import{readNativeOpus,nativeOpusPacket}from'./shared/th06nc/opus-container.mjs';const files=[];for(const directory of ['bgm','bgm2'])for(const file of readdirSync('H:/Games/th/06nc/data/'+directory).filter(f=>f.endsWith('.opus'))){const bytes=readFileSync('H:/Games/th/06nc/data/'+directory+'/'+file),s=readNativeOpus(bytes),digest=createHash('sha256');for(let i=0;i<s.packetCount;i++)digest.update(nativeOpusPacket(s,i));files.push({...s,bytes:undefined,directory,file,sha256:createHash('sha256').update(bytes).digest('hex'),payloadSha256:digest.digest('hex')});}console.log(JSON.stringify(files));
"""
    files=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;current={};read=n.vm+0xf100;seek=n.vm+0xf200;total=0
    def hook(m,a,size,u):
        result=0
        if a==seek:current['position']=m.reg_read(UC_X86_REG_RDX)
        elif a==read:
            position=current['position'];length=m.reg_read(UC_X86_REG_R8)*m.reg_read(UC_X86_REG_RDX);data=current['raw'][position:position+length];m.mem_write(m.reg_read(UC_X86_REG_RCX),data);current['position']+=len(data);result=len(data)
        elif a==0x1402a2740:m.mem_write(m.reg_read(UC_X86_REG_R8),bytes(4));result=n.vm+0x800
        elif a==0x1400f24f0:
            current['allocations']+=1;result=n.vm+(0x1000 if current['allocations']==1 else 0x3000)
        elif a==0x1402a13b0:
            data=bytes(m.mem_read(m.reg_read(UC_X86_REG_RDX),m.reg_read(UC_X86_REG_R8)));current['digest'].update(data);current['packets']+=1;result=960
        m.reg_write(UC_X86_REG_RAX,result);sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [read,seek,0x1402a2740,0x1400f24f0,0x1402a13b0,0x1402bcf20]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    def run(address):
        sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.assets));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.emu_start(address,n.assets,count=10000);assert m.reg_read(UC_X86_REG_RIP)==n.assets;return m.reg_read(UC_X86_REG_EAX)
    for c in files:
        raw=(ROOT.parent.parent/'Games/th/06nc/data'/c['directory']/c['file']).read_bytes();assert hashlib.sha256(raw).hexdigest()==c['sha256'];current.clear();current.update(raw=raw,position=0,allocations=0,digest=hashlib.sha256(),packets=0);m.mem_write(n.owner,bytes(0x98));callbacks=bytearray(56);struct.pack_into('<Q',callbacks,8,seek);struct.pack_into('<Q',callbacks,16,read);m.mem_write(n.vm,bytes(callbacks));m.reg_write(UC_X86_REG_RDX,n.vm);assert run(0x14007ea60)==0,(c['file'],'init')
        channels,preSkip,stride=struct.unpack('<3i',m.mem_read(n.owner+0x40,12));offset,length,samples=struct.unpack('<3q',m.mem_read(n.owner+0x50,24));assert (channels,preSkip,stride,offset,length,samples)==tuple(c[k]for k in ['channels','preSkip','packetStride','dataOffset','dataLength','samples'])
        for i in range(c['packetCount']):assert run(0x14007ec80)==0,(c['file'],i)
        assert run(0x14007ec80)==0xffffffff,(c['file'],'EOF');assert current['digest'].hexdigest()==c['payloadSha256'];assert current['packets']==c['packetCount'];total+=current['packets'];print(c['directory'],c['file'],current['packets'],flush=True)
    assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha
    report=dict(scope=__doc__,files=files,packets=total,sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-opus-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=True,files=len(files),packets=total)))
if __name__=='__main__':main()
