"""Front HUD block init/inactive update, difficulty, labels and stock draw.

Full owner and actual ANMs, signed byte stock edge cases, redraw masks,
forced redraw and protected-life numeric request. GPU/font pixels and active
enemy HP, other HUD fields and complete gameplay are excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/'+s+'.mjs'for s in ['hud-stock','hud-labels','message-state','anm-rebind','anm-vm']];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
    script="""
import{readFileSync}from'node:fs';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{MessageState}from'./shared/th06nc/message-state.mjs';import{initializeHudFront,advanceHudFrontInactive,drawHudStock}from'./shared/th06nc/hud-stock.mjs';import{initializeHudDifficulty,initializeHudModeLabel,drawHudLabels}from'./shared/th06nc/hud-labels.mjs';const hex=b=>Buffer.from(b).toString('hex'),bank=new AnmBank();bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/th06CM.dat/front.anm')),0x620,{slot:13});const state=new MessageState({uniqueScripts:[]},{anmBank:bank,storage:new Uint8Array(0x4228)}),before=hex(state.bytes);initializeHudFront(state);const initialized=hex(state.bytes),updates=[];for(let frame=1;frame<=120;frame++){advanceHudFrontInactive(state);if([1,2,15,30,60,120].includes(frame))updates.push({frame,state:hex(state.bytes)});}const baseline=hex(state.bytes),scenes=[];
for(const lives of [-128,-1,0,1,2,7,8,9,127,128,255])for(const inputFlags of [0,3,12,15])for(const force of [false,true])for(const lifeProtection of [false,true]){state.bytes.set(Buffer.from(baseline,'hex'));const bombs=[0,3,8,255][(lives>>>0)%4],deathCount=(lives*271)|0,calls=[];drawHudStock(state,(vm,r)=>calls.push({kind:'draw',offset:r.offset,state:hex(vm.state)}),{inputFlags,force,lives,bombs,lifeProtection,deathCount,drawNumber:r=>calls.push({kind:'number',...r})});scenes.push({lives,bombs,inputFlags,force,lifeProtection,deathCount,state:hex(state.bytes),calls});}const labelScenes=[];for(const difficulty of [0,1,2,3,4])for(const challengeMode of [false,true])for(const hidden of [false,true])for(const inputFlags of [0,0xffffffff,0x155,0xbeef]){state.bytes.set(Buffer.from(baseline,'hex'));initializeHudDifficulty(state,difficulty);initializeHudModeLabel(state,challengeMode);const selected=hex(state.bytes),calls=[],flags=drawHudLabels(state,(vm,r)=>calls.push({kind:'draw',offset:r.offset,state:hex(vm.state),path:r.path}),{hidden,inputFlags});labelScenes.push({difficulty,challengeMode,hidden,inputFlags,selected,state:hex(state.bytes),calls,flags});}console.log(JSON.stringify({before,initialized,updates,baseline,scenes,labelScenes}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;n.load_title([dict(archive='th06CM.dat',file='front.anm',slot=13,base=0x620)]);calls=[];digest=hashlib.sha256();draws=0;labelMode=False
    def normalize(raw):
        raw=bytearray(raw)
        for offset in range(0xcc0,0x31e0,0x120):
            for field in [0xf0,0xf8]:
                p=offset+field;ptr=struct.unpack_from('<Q',raw,p)[0]
                if ptr:struct.pack_into('<Q',raw,p,ptr-n.assets)
            p=offset+0x100;ptr=struct.unpack_from('<Q',raw,p)[0]
            if ptr:struct.pack_into('<Q',raw,p,(ptr-n.manager-0x608)//64+1)
        return bytes(raw)
    def hook(m,a,size,u):
        sp=m.reg_read(UC_X86_REG_RSP)
        if a in [0x140002a80,0x1400036c0]:
            ptr=m.reg_read(UC_X86_REG_RDX)
            if a==0x1400036c0:assert m.reg_read(UC_X86_REG_R8)&255==1
            else:assert m.reg_read(UC_X86_REG_R8)&255==255 and m.reg_read(UC_X86_REG_R9)&255==255 and bytes(m.mem_read(sp+0x28,1))==b'\1'
            calls.append(dict(kind='draw',offset=ptr-n.owner,state=normalize(bytes(m.mem_read(n.owner,0x4228)))[ptr-n.owner:ptr-n.owner+288].hex()))
            if labelMode:calls[-1]['path']='rotated'if a==0x1400036c0 else'flat'
        else:
            ptr=m.reg_read(UC_X86_REG_R8);assert bytes(m.mem_read(ptr,3))==b'%d\0';calls.append(dict(kind='number',value=m.reg_read(UC_X86_REG_R9D)-(0x100000000 if m.reg_read(UC_X86_REG_R9D)&0x80000000 else 0),format='%d',position=list(struct.unpack('<3f',m.mem_read(m.reg_read(UC_X86_REG_RDX),12)))))
        m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x140002a80,0x1400036c0,0x140009aa0]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    m.mem_write(n.owner,bytes.fromhex(data['before']));m.mem_write(n.vm+0x38,struct.pack('<Q',n.owner));m.reg_write(UC_X86_REG_RBX,n.vm);m.reg_write(UC_X86_REG_R10,n.manager);m.reg_write(UC_X86_REG_R15D,0x620);m.reg_write(UC_X86_REG_EDI,0);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x14003db56,0x14003dbdf,count=1000000);assert normalize(bytes(m.mem_read(n.owner,0x4228))).hex()==data['initialized'],'init'
    byFrame={c['frame']:c for c in data['updates']}
    for frame in range(1,121):
        for reg,value in [(UC_X86_REG_RBX,n.vm),(UC_X86_REG_RSP,n.stack+0x8000),(UC_X86_REG_EDI,0),(UC_X86_REG_ESI,0),(UC_X86_REG_EBP,0)]:m.reg_write(reg,value)
        m.emu_start(0x14003fd10,0x14003ff48,count=1000000)
        if frame in byFrame:assert normalize(bytes(m.mem_read(n.owner,0x4228))).hex()==byFrame[frame]['state'],('update',frame)
    baseline=bytes(m.mem_read(n.owner,0x4228));assert normalize(baseline).hex()==data['baseline']
    for index,s in enumerate(data['scenes']):
        m.mem_write(n.owner,baseline);m.mem_write(n.vm+0x48,struct.pack('<I',s['inputFlags']));m.mem_write(0x140c21dc0,bytes([0x10 if s['force'] else 0]));m.mem_write(0x1404ff0f0,bytes([s['lives']&255,s['bombs']&255]));m.mem_write(0x1404f27c4,bytes([s['lifeProtection']]));m.mem_write(0x1404f1e60,struct.pack('<i',s['deathCount']));m.reg_write(UC_X86_REG_RBX,n.vm);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.reg_write(UC_X86_REG_R12D,0);calls.clear();m.emu_start(0x140040df3,0x140041057,count=1000000);actual=normalize(bytes(m.mem_read(n.owner,0x4228)));assert actual.hex()==s['state'],(index,'owner');assert calls==s['calls'],(index,'calls',calls[:2],s['calls'][:2]);digest.update(actual);draws+=len(calls)
    labelMode=True;labelDraws=0
    for index,s in enumerate(data['labelScenes']):
        m.mem_write(n.owner,baseline);m.mem_write(0x1404f27c0,struct.pack('<i',s['difficulty']));m.reg_write(UC_X86_REG_RDX,n.owner);m.reg_write(UC_X86_REG_RCX,n.manager);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x14003dcc3,0x14003dcde,count=1000000);m.mem_write(0x1404f27c4,bytes([s['challengeMode']]));m.reg_write(UC_X86_REG_RBX,n.vm);m.reg_write(UC_X86_REG_EDI,0);m.emu_start(0x14003dcde,0x14003dd07,count=1000000);assert normalize(bytes(m.mem_read(n.owner,0x4228))).hex()==s['selected'],(index,'difficulty',[(hex(p),a,b)for p,(a,b)in enumerate(zip(normalize(bytes(m.mem_read(n.owner,0x4228))),bytes.fromhex(s['selected'])))if a!=b][:16])
        m.mem_write(n.vm+0x48,struct.pack('<I',s['inputFlags']));m.mem_write(0x140c21dc0,bytes([0x10 if s['hidden'] else 0]));m.reg_write(UC_X86_REG_RBX,n.vm);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);calls.clear();m.emu_start(0x140040b51,0x140040d43,count=1000000);actual=normalize(bytes(m.mem_read(n.owner,0x4228)));assert actual.hex()==s['state'],(index,'label owner');assert calls==s['calls'],(index,'labels');assert struct.unpack('<I',m.mem_read(n.vm+0x48,4))[0]==s['flags'],(index,'flags');digest.update(actual);labelDraws+=len(calls)
    assert {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}==hashes;report=dict(scope=__doc__,scenes=len(data['scenes']),updateFrames=120,updateCheckpoints=len(data['updates']),drawRequests=draws,labelScenes=len(data['labelScenes']),labelDrawRequests=labelDraws,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-hud-stock-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
