"""Spell HUD publication 2787d, strip/font init, update and portrait/name draw.

All seven stage portrait variants and both players, complete HUD owner and
real ANMs. Font paint is a controlled crop service; GPU/glyph pixels and
complete opcode-93 core (covered separately) excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/'+s+'.mjs'for s in ['hud-spell-name','hud-bomb-name','message-state','anm-rebind','anm-vm']];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
    script="""
import{readFileSync}from'node:fs';import{readAnm}from'./shared/th06nc/anm.mjs';import{readEcl}from'./shared/th06nc/ecl.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{MessageState}from'./shared/th06nc/message-state.mjs';import{messageAssetPlan}from'./shared/th06nc/message-layout.mjs';import{initializeSpellNameHud,publishSpellName,finishSpellName,advanceSpellName,drawSpellNameText}from'./shared/th06nc/hud-spell-name.mjs';import{drawHudPortraits}from'./shared/th06nc/hud-bomb-name.mjs';const scenes=[],hex=b=>Buffer.from(b).toString('hex');
for(let stage=1;stage<=7;stage++){const program=readEcl(readFileSync('runtimes/th06nc/artifacts/scripts/th06ST.dat/ecldata'+stage+'.ecl')),requests=new Map();for(const sub of program.subroutines)for(const ins of sub.instructions)if(ins.opcode===93){const a=new DataView(ins.args.buffer,ins.args.byteOffset,ins.args.byteLength),portrait=a.getInt16(0,true),key=new TextDecoder().decode(ins.args.subarray(4,ins.args.indexOf(0,4)));if(!requests.has(portrait))requests.set(portrait,key);}for(const character of [0,1])for(const[portrait,key]of requests)for(const width of [37,280]){
 const refs=[{archive:'th06CM.dat',file:'front.anm',slot:13,base:0x620},...messageAssetPlan(stage,character)],bank=new AnmBank();for(const r of refs)bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+r.archive+'/'+r.file)),r.base,{slot:r.slot});const state=new MessageState({uniqueScripts:[]},{anmBank:bank,storage:new Uint8Array(0x4228)});initializeSpellNameHud(state);const before=hex(state.bytes),events=[];publishSpellName(state,{portrait,key},{publishText:r=>{events.push({offset:r.offset,key:r.key,colors:r.colors});const vm=state.vm(r.offset);[1,1,width,36].forEach((n,i)=>vm.v.setInt32(0x10c+i*4,n,true));vm.v.setUint32(0xc4,vm.v.getUint32(0xc4,true)|1,true);}});const published={state:hex(state.bytes),events},frames=[];
 for(let frame=1;frame<=240;frame++){if(frame===120)finishSpellName(state);advanceSpellName(state);const calls=[];drawHudPortraits(state,(vm,r)=>calls.push({kind:'draw',offset:r.offset,state:hex(vm.state)}),{setupCamera:r=>calls.push({kind:'camera',...r})});drawSpellNameText(state,(vm,r)=>calls.push({kind:'draw',offset:r.offset,state:hex(vm.state)}));if([1,2,15,30,60,119,120,121,180,240].includes(frame))frames.push({frame,state:hex(state.bytes),calls});}scenes.push({stage,character,portrait,key,width,refs,before,published,frames});}}console.log(JSON.stringify(scenes));
"""
    scenes=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;events=[];calls=[];digest=hashlib.sha256();checked=0
    def normalize(raw):
        raw=bytearray(raw)
        for offset in [0x838,0x3da0,0x4108]:
            for field in [0xf0,0xf8]:
                p=offset+field;ptr=struct.unpack_from('<Q',raw,p)[0]
                if ptr:struct.pack_into('<Q',raw,p,ptr-next(lo for lo,hi in n.ranges if lo<=ptr<hi))
            p=offset+0x100;ptr=struct.unpack_from('<Q',raw,p)[0]
            if ptr:struct.pack_into('<Q',raw,p,(ptr-n.manager-0x608)//64+1)
        return bytes(raw)
    def relocate(raw):
        raw=bytearray(raw)
        for field in [0xf0,0xf8]:
            p=0x3da0+field;ptr=struct.unpack_from('<Q',raw,p)[0]
            if ptr:struct.pack_into('<Q',raw,p,ptr+n.assets)
        p=0x3da0+0x100;ptr=struct.unpack_from('<Q',raw,p)[0]
        if ptr:struct.pack_into('<Q',raw,p,n.manager+0x608+(ptr-1)*64)
        return bytes(raw)
    def hook(m,a,size,u):
        sp=m.reg_read(UC_X86_REG_RSP)
        if a==0x140007530:
            ptr=m.reg_read(UC_X86_REG_RDX);keyPtr=struct.unpack('<Q',m.mem_read(sp+0x38,8))[0];key=bytes(m.mem_read(keyPtr,100)).split(b'\0')[0].decode();colors=[m.reg_read(UC_X86_REG_R8D),m.reg_read(UC_X86_REG_R9D),*struct.unpack('<2I',m.mem_read(sp+0x28,4)+m.mem_read(sp+0x30,4))];events.append(dict(offset=ptr-n.owner,key=key,colors=colors));m.mem_write(ptr+0x10c,struct.pack('<4i',1,1,currentWidth,36));flags=struct.unpack('<I',m.mem_read(ptr+0xc4,4))[0];m.mem_write(ptr+0xc4,struct.pack('<I',flags|1))
        elif a==0x14007af40:calls.append(dict(kind='camera',minZ=struct.unpack('<f',struct.pack('<I',m.reg_read(UC_X86_REG_XMM1)&0xffffffff))[0],maxZ=struct.unpack('<f',struct.pack('<I',m.reg_read(UC_X86_REG_XMM2)&0xffffffff))[0]))
        else:
            ptr=m.reg_read(UC_X86_REG_RDX);offset=ptr-n.owner;raw=normalize(bytes(m.mem_read(n.owner,0x4228)));calls.append(dict(kind='draw',offset=offset,state=raw[offset:offset+288].hex()))
        m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x140007530,0x14007af40,0x1400067f0]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    def run(address,rcx):
        sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,rcx);m.emu_start(address,n.stack+0xf000,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000
    for index,s in enumerate(scenes):
        currentWidth=s['width'];n.load_title(s['refs']);m.mem_write(n.owner,relocate(bytes.fromhex(s['before'])));m.mem_write(n.vm+0x38,struct.pack('<Q',n.owner));m.mem_write(0x140a6ec08,struct.pack('<Q',n.owner));m.reg_write(UC_X86_REG_RBX,n.vm);m.reg_write(UC_X86_REG_R10,n.manager);m.reg_write(UC_X86_REG_EDI,0);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x14003dff3,0x14003e056,count=1000000);m.emu_start(0x14003e0c4,0x14003e0da,count=1000000);assert normalize(bytes(m.mem_read(n.owner,0x4228))).hex()==s['before'],(index,'init');m.mem_write(n.vm+0x5000,struct.pack('<h',s['portrait']));m.mem_write(n.vm+0x5100,s['key'].encode()+b'\0');m.reg_write(UC_X86_REG_RSI,n.vm+0x5000);m.reg_write(UC_X86_REG_R15,n.vm+0x5100);m.reg_write(UC_X86_REG_R12D,0);events.clear();m.emu_start(0x14002787d,0x1400279a3,count=1000000);actual=normalize(bytes(m.mem_read(n.owner,0x4228)));assert actual.hex()==s['published']['state'],(index,'publish');assert events==s['published']['events'],(index,'font');byFrame={c['frame']:c for c in s['frames']}
        for frame in range(1,241):
            if frame==120:m.mem_write(n.owner+0x8c2,struct.pack('<h',1))
            m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.reg_write(UC_X86_REG_RBX,n.vm);m.emu_start(0x14003ffa4,0x14003ffd2,count=1000000);calls.clear();run(0x14003cca0,n.vm);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.reg_write(UC_X86_REG_RDI,n.vm);m.emu_start(0x140041987,0x140041abb,count=1000000)
            if frame not in byFrame:continue
            c=byFrame[frame];actual=normalize(bytes(m.mem_read(n.owner,0x4228)));assert actual.hex()==c['state'],(index,frame,'owner');assert calls==c['calls'],(index,frame,'draw');digest.update(actual);checked+=1
    assert {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}==hashes;report=dict(scope=__doc__,scenes=len(scenes),frames=len(scenes)*240,checkpoints=checked,portraitVariants=len({(s['stage'],s['portrait'])for s in scenes}),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-hud-spell-name-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
