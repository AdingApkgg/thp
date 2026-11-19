"""Power HUD init 3dd07 and draw 41057..413c0 with real front ANMs.

Complete HUD owner, saved metrics, four complete shared sprite-cache entries,
draw VM requests and numeric output. Continuous partial/full/back transitions;
GPU pixels and missing/unloaded front resources excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/'+s+'.mjs'for s in ['hud-power','hud-stock','sprite-layout','anm-bank','anm-vm']];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
    script="""
import{readFileSync}from'node:fs';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{MessageState}from'./shared/th06nc/message-state.mjs';import{initializeHudFront,advanceHudFrontInactive}from'./shared/th06nc/hud-stock.mjs';import{initializeHudPower,drawHudPower}from'./shared/th06nc/hud-power.mjs';import{spriteLogicalSize}from'./shared/th06nc/sprite-layout.mjs';const F=Math.fround,hex=b=>Buffer.from(b).toString('hex'),resource=readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/th06CM.dat/front.anm')),original=JSON.stringify(resource),scenes=[];
function cache(bank){const bytes=new Uint8Array(256),v=new DataView(bytes.buffer);for(let i=0;i<4;i++){const s=bank.sprites.get(1599+i).sprite,p=i*64,right=F(s.x+s.width),bottom=F(s.y+s.height),width=F(right-s.x),height=F(bottom-s.y),[logicalHeight,logicalWidth]=spriteLogicalSize(s);for(const[o,x]of[[0,F(s.x/resource.width)],[4,F(s.y/resource.height)],[8,F(right/resource.width)],[12,F(bottom/resource.height)],[20,height],[24,width],[28,logicalHeight],[32,logicalWidth],[40,resource.height],[44,resource.width],[48,s.x],[52,s.y],[56,right],[60,bottom]])v.setFloat32(p+o,x,true);v.setInt32(p+16,s.id,true);v.setInt32(p+36,13,true);}return hex(bytes);}
for(const inputFlags of [0,0x10,0x20,0x30,0xbeef])for(const force of [false,true])for(const preFrames of [0,60]){
 const bank=new AnmBank();bank.load(resource,0x620,{slot:13});const state=new MessageState({uniqueScripts:[]},{anmBank:bank,storage:new Uint8Array(0x4228)});initializeHudFront(state);const before=hex(state.bytes),metrics=initializeHudPower(state),initial=hex(state.bytes),initialCache=cache(bank);for(let i=0;i<preFrames;i++)advanceHudFrontInactive(state);const frames=[];
 for(const playerPower of [0,1,15,16,31,32,63,64,127,128,129,65535,127,64,1,0,128,0]){const calls=[];drawHudPower(state,(vm,r)=>calls.push({kind:'draw',offset:r.offset,state:hex(vm.state)}),{inputFlags,force,playerPower,drawNumber:r=>calls.push({kind:'number',...r})});frames.push({playerPower,state:hex(state.bytes),cache:cache(bank),calls});}if(JSON.stringify(resource)!==original)throw Error('Shared source resource mutated');scenes.push({inputFlags,force,preFrames,before,initial,initialCache,metrics,frames});}console.log(JSON.stringify(scenes));
"""
    scenes=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;calls=[];digest=hashlib.sha256();draws=0
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
        if a==0x140002a80:
            ptr=m.reg_read(UC_X86_REG_RDX);assert m.reg_read(UC_X86_REG_R8)&255==255 and m.reg_read(UC_X86_REG_R9)&255==255 and bytes(m.mem_read(sp+0x28,1))==b'\1';calls.append(dict(kind='draw',offset=ptr-n.owner,state=normalize(bytes(m.mem_read(n.owner,0x4228)))[ptr-n.owner:ptr-n.owner+288].hex()))
        else:
            ptr=m.reg_read(UC_X86_REG_R8);assert bytes(m.mem_read(ptr,3))==b'%d\0';value=str(m.reg_read(UC_X86_REG_R9D));calls.append(dict(kind='number',value=value,text=value,format='%d',position=list(struct.unpack('<3f',m.mem_read(m.reg_read(UC_X86_REG_RDX),12)))))
        m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x140002a80,0x140009aa0]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    for index,s in enumerate(scenes):
        m.mem_write(n.manager+0x270e0,bytes(4));n.load_title([dict(archive='th06CM.dat',file='front.anm',slot=13,base=0x620)]);m.mem_write(n.owner,bytes(0x4228));m.mem_write(n.owner+0x36b0,struct.pack('<i',-1));m.mem_write(n.owner+0x38f8,struct.pack('<Q',1));m.mem_write(n.owner+0x3b58,struct.pack('<Q',1));m.mem_write(n.vm,bytes(0x100));m.mem_write(n.vm+0x38,struct.pack('<Q',n.owner));m.reg_write(UC_X86_REG_RBX,n.vm);m.reg_write(UC_X86_REG_R10,n.manager);m.reg_write(UC_X86_REG_R15D,0x620);m.reg_write(UC_X86_REG_EDI,0);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x14003db56,0x14003dbdf,count=1000000);assert normalize(bytes(m.mem_read(n.owner,0x4228))).hex()==s['before'],(index,'front init')
        m.reg_write(UC_X86_REG_XMM1,struct.unpack('<I',struct.pack('<f',700))[0]);m.emu_start(0x14003dd07,0x14003ddd6,count=1000000);assert normalize(bytes(m.mem_read(n.owner,0x4228))).hex()==s['initial'],(index,'init');assert bytes(m.mem_read(n.manager+0x608+1599*64,256)).hex()==s['initialCache'],(index,'cache init',[(hex(p),a,b)for p,(a,b)in enumerate(zip(bytes(m.mem_read(n.manager+0x608+1599*64,256)),bytes.fromhex(s['initialCache'])))if a!=b][:16])
        expectedMetrics=struct.pack('<iff2f',s['metrics']['spriteId'],s['metrics']['marginX'],s['metrics']['marginY'],s['metrics']['pixelWidth'],s['metrics']['logicalWidth']);assert bytes(m.mem_read(n.vm+0x24,20))==expectedMetrics,(index,'metrics')
        for frame in range(s['preFrames']):
            for reg,value in [(UC_X86_REG_RBX,n.vm),(UC_X86_REG_RSP,n.stack+0x8000),(UC_X86_REG_EDI,0),(UC_X86_REG_ESI,0),(UC_X86_REG_EBP,0)]:m.reg_write(reg,value)
            m.emu_start(0x14003fd10,0x14003ff48,count=1000000)
        for c in s['frames']:
            m.mem_write(n.vm+0x48,struct.pack('<I',s['inputFlags']));m.mem_write(0x140c21dc0,bytes([0x10 if s['force'] else 0]));m.mem_write(0x1404f1e88,struct.pack('<H',c['playerPower']));m.reg_write(UC_X86_REG_RBX,n.vm);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.reg_write(UC_X86_REG_R15D,128);calls.clear();m.emu_start(0x140041057,0x1400413c0,count=1000000);actual=normalize(bytes(m.mem_read(n.owner,0x4228)));assert actual.hex()==c['state'],(index,c['playerPower'],'owner',[(hex(p),a,b)for p,(a,b)in enumerate(zip(actual,bytes.fromhex(c['state'])))if a!=b][:16]);cache=bytes(m.mem_read(n.manager+0x608+1599*64,256));assert cache.hex()==c['cache'],(index,c['playerPower'],'cache');assert calls==c['calls'],(index,c['playerPower'],'calls',calls[:1],c['calls'][:1]);digest.update(actual);digest.update(cache);draws+=len(calls)
    assert {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}==hashes;report=dict(scope=__doc__,scenes=len(scenes),drawFrames=sum(len(s['frames'])for s in scenes),drawRequests=draws,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-hud-power-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
