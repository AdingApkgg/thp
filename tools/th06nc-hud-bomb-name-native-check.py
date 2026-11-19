"""Bomb-name publication 3d370, strip init 3df89, portrait/text draw and update.

Real portrait/text ANMs and complete 4228-byte owner. Font painting is an
observed service with controlled crop metrics; no glyph/GPU equivalence claim.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/'+s+'.mjs'for s in ['hud-bomb-name','message-state','anm-rebind','anm-vm','sound-queue']];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
    script="""
import{readFileSync}from'node:fs';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{MessageState}from'./shared/th06nc/message-state.mjs';import{publishBombName,finishBombName,advanceBombName,drawHudPortraits,initializeBombNameHud,drawBombNameText}from'./shared/th06nc/hud-bomb-name.mjs';const scenes=[],hex=b=>Buffer.from(b).toString('hex');
for(const character of [0,1])for(const resourceSlot of [16,17])for(const soundDisabled of [false,true])for(const initialSound of [[-1,-1,-1],[-1,14,-1],[14,7,-1],[1,2,3]]){
 const refs=[{archive:'th06CM.dat',file:'front.anm',slot:13,base:0x620},{archive:'th06IN.dat',file:'text.anm',slot:0,base:0x72f},...['a','b','c'].map((suffix,i)=>({archive:'th06CM.dat',file:'face0'+character+suffix+'.anm',slot:15+i,base:0x4c0+i*2}))],bank=new AnmBank();for(const r of refs)bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+r.archive+'/'+r.file)),r.base,{slot:r.slot});const environment={bombCaptionMode:99},state=new MessageState({uniqueScripts:[]},{anmBank:bank,environment,storage:new Uint8Array(0x4228)}),sounds=[...initialSound],key='EXE_'+(character?'MARISA':'REIMU')+'_'+(resourceSlot===16?'A':'B')+'_BOMB_NAME',events=[];initializeBombNameHud(state);const before=hex(state.bytes);
 publishBombName(state,{key,resourceSlot},{soundSlots:sounds,soundDisabled,publishText:r=>{events.push({offset:r.offset,key:r.key,colors:r.colors});const vm=state.vm(r.offset);[1,1,200,36].forEach((n,i)=>vm.v.setInt32(0x10c+i*4,n,true));vm.v.setUint32(0xc4,vm.v.getUint32(0xc4,true)|1,true);}});const published={state:hex(state.bytes),sounds:[...sounds],events,mode:environment.bombCaptionMode},frames=[];
 for(let frame=1;frame<=180;frame++){if(frame===90)finishBombName(state);advanceBombName(state);const calls=[];drawHudPortraits(state,(vm,r)=>calls.push({kind:'draw',offset:r.offset,state:hex(vm.state)}),{setupCamera:r=>calls.push({kind:'camera',...r})});drawBombNameText(state,(vm,r)=>calls.push({kind:'draw',offset:r.offset,state:hex(vm.state)}));if([1,2,15,30,60,89,90,91,120,180].includes(frame))frames.push({frame,state:hex(state.bytes),calls});}scenes.push({refs,character,resourceSlot,soundDisabled,initialSound,key,before,published,frames});
}console.log(JSON.stringify(scenes));
"""
    scenes=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;events=[];calls=[];digest=hashlib.sha256();checked=0
    def normalize(raw):
        raw=bytearray(raw)
        for offset in [0x718,0x3c80,0x3fe8,0x4108]:
            for field in [0xf0,0xf8]:
                p=offset+field;ptr=struct.unpack_from('<Q',raw,p)[0]
                if ptr:struct.pack_into('<Q',raw,p,ptr-next(lo for lo,hi in n.ranges if lo<=ptr<hi))
            p=offset+0x100;ptr=struct.unpack_from('<Q',raw,p)[0]
            if ptr:struct.pack_into('<Q',raw,p,(ptr-n.manager-0x608)//64+1)
        return bytes(raw)
    def hook(m,a,size,u):
        sp=m.reg_read(UC_X86_REG_RSP)
        if a==0x140007530:
            ptr=m.reg_read(UC_X86_REG_RDX);keyPtr=struct.unpack('<Q',m.mem_read(sp+0x38,8))[0];key=bytes(m.mem_read(keyPtr,80)).split(b'\0')[0].decode();colors=[m.reg_read(UC_X86_REG_R8D),m.reg_read(UC_X86_REG_R9D),*struct.unpack('<2I',m.mem_read(sp+0x28,4)+m.mem_read(sp+0x30,4))];events.append(dict(offset=ptr-n.owner,key=key,colors=colors));m.mem_write(ptr+0x10c,struct.pack('<4i',1,1,200,36));flags=struct.unpack('<I',m.mem_read(ptr+0xc4,4))[0];m.mem_write(ptr+0xc4,struct.pack('<I',flags|1))
        elif a==0x14007af40:calls.append(dict(kind='camera',minZ=struct.unpack('<f',struct.pack('<I',m.reg_read(UC_X86_REG_XMM1)&0xffffffff))[0],maxZ=struct.unpack('<f',struct.pack('<I',m.reg_read(UC_X86_REG_XMM2)&0xffffffff))[0]))
        else:
            ptr=m.reg_read(UC_X86_REG_RDX);offset=ptr-n.owner;raw=normalize(bytes(m.mem_read(n.owner,0x4228)));calls.append(dict(kind='draw',offset=offset,state=raw[offset:offset+288].hex()))
        m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x140007530,0x14007af40,0x1400067f0]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    def run(address,rcx):
        sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,rcx);m.emu_start(address,n.stack+0xf000,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000
    for index,s in enumerate(scenes):
        n.load_title(s['refs']);initial=bytearray.fromhex(s['before'])
        for field in [0xf0,0xf8]:
            ptr=struct.unpack_from('<Q',initial,0x3c80+field)[0]
            if ptr:struct.pack_into('<Q',initial,0x3c80+field,ptr+n.assetByFile['front.anm'])
        ptr=struct.unpack_from('<Q',initial,0x3d80)[0]
        if ptr:struct.pack_into('<Q',initial,0x3d80,n.manager+0x608+(ptr-1)*64)
        m.mem_write(n.owner,bytes(initial));m.mem_write(n.vm+0x38,struct.pack('<Q',n.owner));m.mem_write(0x140a6ec08,struct.pack('<Q',n.owner));m.mem_write(0x140509670,struct.pack('<3i',*s['initialSound']));m.mem_write(0x140509694,bytes([s['soundDisabled']]));m.mem_write(0x140c21974,struct.pack('<i',99));m.mem_write(n.vm+0x5000,s['key'].encode()+b'\0');m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.reg_write(UC_X86_REG_RBX,n.vm);m.reg_write(UC_X86_REG_EDI,0);m.emu_start(0x14003df89,0x14003dff3,count=1000000);assert normalize(bytes(m.mem_read(n.owner,0x4228))).hex()==s['before'],(index,'strip initialization');events.clear();m.reg_write(UC_X86_REG_EDX,0x4c2+(s['resourceSlot']-16)*2+1);m.reg_write(UC_X86_REG_R8,n.vm+0x5000);run(0x14003d370,n.manager);actual=normalize(bytes(m.mem_read(n.owner,0x4228)));assert actual.hex()==s['published']['state'],(index,'publish',[(hex(p),a,b)for p,(a,b)in enumerate(zip(actual,bytes.fromhex(s['published']['state'])))if a!=b][:30]);assert events==s['published']['events'],(index,events,s['published']['events']);assert list(struct.unpack('<3i',m.mem_read(0x140509670,12)))==s['published']['sounds'];assert struct.unpack('<i',m.mem_read(0x140c21974,4))[0]==s['published']['mode'];byFrame={c['frame']:c for c in s['frames']}
        for frame in range(1,181):
            if frame==90:m.mem_write(n.owner+0x7a2,struct.pack('<h',1))
            m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.reg_write(UC_X86_REG_RBX,n.vm);m.emu_start(0x14003ff76,0x14003ffa4,count=1000000);calls.clear();run(0x14003cca0,n.vm);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.reg_write(UC_X86_REG_RDI,n.vm);m.emu_start(0x140041987,0x140041a29,count=1000000)
            if frame not in byFrame:continue
            c=byFrame[frame];actual=normalize(bytes(m.mem_read(n.owner,0x4228)));assert actual.hex()==c['state'],(index,frame,'owner');assert calls==c['calls'],(index,frame,'draw');digest.update(actual);checked+=1
    assert {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}==hashes;report=dict(scope=__doc__,scenes=len(scenes),frames=len(scenes)*180,checkpoints=checked,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-hud-bomb-name-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
