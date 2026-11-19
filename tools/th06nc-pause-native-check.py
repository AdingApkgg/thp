"""Pause owner a120/aee0: normal-game input, ANM, confirmation and draw.

Whole da0-byte owner, native resource bindings, font requests and draw VMs.
Localization lookup/font paint use controlled boundaries; music is not exercised;
screenshot capture, other mode handoffs, GPU pixels and whole game excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/'+s+'.mjs'for s in ['pause-menu','anm-bank','anm-rebind','anm-vm','fade','sound-queue']];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
    script="""
import{readFileSync}from'node:fs';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{PauseMenu,pauseAsset}from'./shared/th06nc/pause-menu.mjs';import{NativeFade}from'./shared/th06nc/fade.mjs';const refs=[pauseAsset,{archive:'th06IN.dat',file:'text.anm',slot:0,base:0x72f}],scenes=[],hex=b=>Buffer.from(b).toString('hex');
const paths=[{},{2:256,4:32,5:16,8:48,16:256},{16:256},{16:1024},{10:32,16:256,24:16,32:256},{10:32,14:32,20:256,28:16,36:256},{10:32,16:256,24:256,40:1024},{10:32,16:256,24:16,32:512,40:1024},{16:2048},{16:16384},{10:16,16:256,24:32,32:512,40:1024},{10:48,16:256}];
for(const path of paths)for(const reopen of [false,true])for(const soundDisabled of [false,true])for(const initialSounds of [[-1,-1,-1],[12,10,11]]){const bank=new AnmBank();for(const r of refs)bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+r.archive+'/'+r.file)),r.base,{slot:r.slot});const fade=new NativeFade(),font=[],sounds=[...initialSounds],menu=new PauseMenu(bank,{fade,soundSlots:sounds,soundDisabled,publishText:(vm,r)=>{font.push({offset:vm.state.byteOffset,key:r.key,colors:r.colors});[1,1,120,36].forEach((x,i)=>vm.v.setInt32(0x10c+i*4,x,true));vm.v.setUint32(0xc4,vm.v.getUint32(0xc4,true)|1,true);}}),frames=[];let previous=0;for(let frame=1;frame<=120;frame++){const opened=!menu.active;if(opened)menu.active=true;const held=path[frame]??0;font.length=0;fade.tick();menu.tick({held,previous});previous=held;const calls=[];menu.draw((vm,r)=>calls.push({offset:r.offset,state:hex(vm.state)}));frames.push({frame,held,opened,state:hex(menu.bytes),active:menu.active,event:menu.event,font:[...font],sounds:[...sounds],fade:hex(fade.state),calls});if(!menu.active&&!reopen)break;}scenes.push({path,reopen,soundDisabled,initialSounds,frames});}console.log(JSON.stringify({refs,scenes}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;n.load_title(data['refs']);events=[];draws=[];digest=hashlib.sha256();checked=0
    def normal_vm(raw):
        raw=bytearray(raw)
        for p in [0xf0,0xf8]:
            ptr=struct.unpack_from('<Q',raw,p)[0]
            if ptr:struct.pack_into('<Q',raw,p,ptr-next(lo for lo,hi in n.ranges if lo<=ptr<hi))
        ptr=struct.unpack_from('<Q',raw,0x100)[0]
        if ptr:struct.pack_into('<Q',raw,0x100,(ptr-n.manager-0x608)//64+1)
        return raw
    def normalize():
        raw=bytearray(m.mem_read(n.owner,0xda0))
        for p in [*range(0,10*288,288),0xb50,0xc70]:raw[p:p+288]=normal_vm(raw[p:p+288])
        return bytes(raw)
    def hook(m,a,size,u):
        sp=m.reg_read(UC_X86_REG_RSP)
        if a==0x140009d3a:m.reg_write(UC_X86_REG_RIP,0x140009e05);return
        if a==0x140007530:
            ptr=m.reg_read(UC_X86_REG_RDX);keyPtr=struct.unpack('<Q',m.mem_read(sp+0x38,8))[0];key=bytes(m.mem_read(keyPtr,100)).split(b'\0')[0].decode();colors=[m.reg_read(UC_X86_REG_R8D),m.reg_read(UC_X86_REG_R9D),*struct.unpack('<2I',m.mem_read(sp+0x28,4)+m.mem_read(sp+0x30,4))];events.append(dict(offset=ptr-n.owner,key=key,colors=colors));m.mem_write(ptr+0x10c,struct.pack('<4i',1,1,120,36));flags=struct.unpack('<I',m.mem_read(ptr+0xc4,4))[0];m.mem_write(ptr+0xc4,struct.pack('<I',flags|1))
        elif a==0x1400067f0:
            ptr=m.reg_read(UC_X86_REG_RDX);raw=normal_vm(bytes(m.mem_read(ptr,288)));id=struct.unpack_from('<H',raw,0x38)[0];sprite=struct.unpack_from('<H',raw,0x34)[0];offset={0x76b:0,0x76e:0x360,0x76f:0x480,0x770:0x5a0,0x773:0xc70}.get(id,(sprite-0x740+6)*288);draws.append(dict(offset=offset,state=raw.hex()))
        elif a in [0x14007af40,0x1402bcf20]:pass
        else:raise AssertionError(hex(a))
        m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x140009d3a,0x140007530,0x1400067f0,0x14007af40,0x1402bcf20]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    def run(address,rcx):
        sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,rcx);m.emu_start(address,n.stack+0xf000,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000
    for index,s in enumerate(data['scenes']):
        m.mem_write(n.owner,bytes(0xda0));m.mem_write(n.vm,bytes(0x10000));m.mem_write(0x1404f278c,b'\0');m.mem_write(0x1404f27b4,b'\0\0');m.mem_write(0x1404f27b0,b'\1');m.mem_write(0x140c21e03,b'\0');m.mem_write(0x140509660,struct.pack('<i',-1));m.mem_write(0x140509670,struct.pack('<3i',*s['initialSounds']));m.mem_write(0x140509694,bytes([s['soundDisabled']]));m.mem_write(0x140c22158,struct.pack('<Q',n.vm));m.mem_write(0x140a6ec60,struct.pack('<2I',0,0));m.mem_write(0x140c21d9c,bytes(4))
        previous=0
        for c in s['frames']:
            frame=c['frame'];
            if c['opened']:m.mem_write(0x1404f27b0,b'\1')
            m.mem_write(0x140a6ec60,struct.pack('<2I',c['held'],previous));previous=c['held'];events.clear();run(0x140075af0,n.vm);run(0x14000a120,n.owner);assert events==c['font'],(index,frame,'font',events,c['font']);draws.clear();draw_offsets=[r['offset']for r in c['calls']];run(0x14000aee0,n.owner)
            actual=normalize();expected=bytes.fromhex(c['state'])
            if actual!=expected:
                (ROOT/'tools/tmp/th06nc-pause-native.bin').write_bytes(actual);(ROOT/'tools/tmp/th06nc-pause-js.bin').write_bytes(expected);diff=[hex(i)for i,(a,b)in enumerate(zip(actual,expected))if a!=b];raise AssertionError((index,frame,'owner',diff[:30],[(p,actual[int(p,16)],expected[int(p,16)])for p in diff[:10]]))
            
            if c['event']:assert struct.unpack('<i',m.mem_read(0x140c21d9c,4))[0]==(12 if c['event']['kind']=='restart' else 1),(index,frame,'supervisor request')
            assert bool(m.mem_read(0x1404f27b0,1)[0])==c['active'],(index,frame,'active');assert draws==c['calls'],(index,frame,'draw',[(r['offset'])for r in draws],[(r['offset'])for r in c['calls']],[(i,next((hex(j)for j,(a,b)in enumerate(zip(bytes.fromhex(a['state']),bytes.fromhex(b['state'])))if a!=b),None))for i,(a,b)in enumerate(zip(draws,c['calls']))if a!=b]);assert list(struct.unpack('<3i',m.mem_read(0x140509670,12)))==c['sounds'],(index,frame,'sounds');assert bytes(m.mem_read(n.vm,56)).hex()==c['fade'],(index,frame,'fade');digest.update(actual);checked+=1
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items());report=dict(scope=__doc__,scenes=len(data['scenes']),frames=checked,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-pause-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
