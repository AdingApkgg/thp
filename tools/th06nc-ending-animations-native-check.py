"""Ending VM adapters through real 2760/2a20/2980 and 69b0.

All Staff programs and eight text programs compare complete VM bytes through
initial binding and 120 updates from three controlled previous states. Native
loader links original resources. Text-cache pointers explicitly reference original
text programs; actual font-cache producer/publication and GPU are excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/'+s+'.mjs'for s in ['ending-animations','anm-rebind','anm-bank','anm-vm','anm-command','anm-frame']];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources};script="""
import{readFileSync}from'node:fs';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{EndingAnimations}from'./shared/th06nc/ending-animations.mjs';const refs=[{archive:'th06ED.dat',file:'staff01.anm',slot:49,base:0x620},{archive:'th06ED.dat',file:'staff02.anm',slot:50,base:0x627},{archive:'th06ED.dat',file:'staff03.anm',slot:51,base:0x62e},{archive:'th06IN.dat',file:'text.anm',slot:0,base:0x72f}],bank=new AnmBank();for(const r of refs)bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+r.archive+'/'+r.file)),r.base,{slot:r.slot});const hex=b=>Buffer.from(b).toString('hex'),cases=[];for(const text of [false,true])for(const id of text?Array.from({length:8},(_,i)=>0x737+i*2):Array.from({length:10},(_,i)=>0x620+i))for(let prior=0;prior<3;prior++){const owner=new EndingAnimations(bank),raw=owner.slot(0x38),v=new DataView(raw.buffer,raw.byteOffset,raw.byteLength);for(const p of [0x18,0x1c,0x20,0xc8,0xcc,0xd0])v.setFloat32(p,(p+1)*0.25+prior,true);v.setUint32(0xc4,0x4001,true);v.setUint16(0x108,prior===1?0x1010:0xf0f,true);v.setUint32(0x10c,77,true);const before=hex(raw);const vm=text?owner.prepareText(0x38,id):owner.bind(0x38,id);const initial=hex(raw),sprite=text?null:0x630;if(sprite!==null)owner.bindSprite(0x38,sprite);const rebound=hex(raw),frames=[];for(let frame=0;frame<120;frame++){owner.tick(0x38);frames.push(hex(raw));}cases.push({id,text,before,initial,sprite,rebound,frames});}console.log(JSON.stringify({refs,cases}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));hashes.update({('runtimes/th06nc/artifacts/scripts/'+r['archive']+'/'+r['file']):hashlib.sha256((ROOT/('runtimes/th06nc/artifacts/scripts/'+r['archive']+'/'+r['file'])).read_bytes()).hexdigest()for r in data['refs']});n=Native();n.load_title(data['refs']);m=n.m;digest=hashlib.sha256();ticks=0
    def call(start):
        sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.emu_start(start,n.stack+0xf000,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000,hex(start)
    def normalize():
        b=bytearray(m.mem_read(n.vm,288))
        for p in [0xf0,0xf8]:
            ptr=struct.unpack_from('<Q',b,p)[0]
            if ptr:
                base=next(base for base,end in n.ranges if base<=ptr<end);struct.pack_into('<Q',b,p,ptr-base)
        ptr=struct.unpack_from('<Q',b,0x100)[0]
        if ptr:struct.pack_into('<Q',b,0x100,(ptr-n.manager-0x608)//64+1)
        return bytes(b)
    for i,c in enumerate(data['cases']):
        m.mem_write(n.vm,bytes.fromhex(c['before']));m.reg_write(UC_X86_REG_RCX,n.manager);m.reg_write(UC_X86_REG_RDX,n.vm);m.reg_write(UC_X86_REG_R8,c['id'])
        if c['text']:
            m.mem_write(n.vm+0x38,struct.pack('<H',c['id']));ptr=struct.unpack('<Q',m.mem_read(n.manager+0x23090+c['id']*8,8))[0];m.reg_write(UC_X86_REG_R8,ptr)
        call(0x140002a20 if c['text']else 0x140002760);actual=normalize();assert actual==bytes.fromhex(c['initial']),(i,'initial',[(hex(p),a,b)for p,(a,b)in enumerate(zip(actual,bytes.fromhex(c['initial'])))if a!=b][:8]);digest.update(actual)
        if c['sprite']is not None:
            m.reg_write(UC_X86_REG_RCX,n.manager);m.reg_write(UC_X86_REG_RDX,n.vm);m.reg_write(UC_X86_REG_R8,c['sprite']);call(0x140002980);actual=normalize();assert actual==bytes.fromhex(c['rebound']),(i,'sprite');digest.update(actual)
        for frame,expected in enumerate(c['frames']):
            m.reg_write(UC_X86_REG_RCX,n.manager);m.reg_write(UC_X86_REG_RDX,n.vm);call(0x1400069b0);actual=normalize();assert actual==bytes.fromhex(expected),(i,frame,'VM');digest.update(actual);ticks+=1
    assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in hashes}
    report=dict(scope=__doc__,cases=len(data['cases']),ticks=ticks,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-ending-animations-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'cases':len(data['cases']),'ticks':ticks}))
if __name__=='__main__':main()
