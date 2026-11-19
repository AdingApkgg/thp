"""ASCII manager 9790 init, formatted cache copy 9b07 and full draw 9890.

Complete owner, cache, VM and camera/glyph requests. Preformatted Latin-1
records exercise newline, spaces, invalid glyphs, alternate atlas, scales,
colors, mode switches and capacity. CRT formatting and GPU pixels excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/ascii-text.mjs','shared/th06nc/score-popup-draw.mjs','shared/th06nc/ascii-layout.mjs'];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
    script=r"""
import{asciiFontAssets}from'./shared/th06nc/ascii-layout.mjs';import{readFileSync}from'node:fs';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{createAsciiTextState,enqueueAsciiText,drawAsciiText}from'./shared/th06nc/ascii-text.mjs';const hex=b=>Buffer.from(b).toString('hex'),bank=new AnmBank();for(const r of asciiFontAssets)bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+r.archive+'/'+r.file)),r.base,{slot:r.slot});const scenes=[];
for(const cursor of [0,255,256])for(const alternate of [false,true]){const state=createAsciiTextState(bank),initial=hex(state.bytes);state.v.setInt32(0x7bb0,cursor,true);const requests=[],checkpoints=[];for(let i=0;i<4;i++){const text=['000123450','A -12.5%\n +9',String.fromCharCode(1,31,32,33,126,129,130,255),''][i],request={text,position:[723.25+i,78.5-i,.49],scale:[1+i*.25,.5+i*.25],color:[0xffffffff,0x80ff4080,0,0xff00ffff][i],camera:i&1,alternate:Number(alternate)};state.v.setFloat32(0,request.scale[0],true);state.v.setFloat32(4,request.scale[1],true);state.v.setUint32(0x52cc,request.color,true);state.bytes[0x52c8]=request.camera;state.bytes[0x52c9]=request.alternate;const accepted=enqueueAsciiText(state,{text,position:request.position});requests.push(request);checkpoints.push({accepted,state:hex(state.bytes)});}const calls=[];drawAsciiText(state,(vm,r)=>calls.push({kind:'draw',state:hex(vm.state)}),{setupCamera:r=>calls.push({kind:'camera',...r})});scenes.push({cursor,alternate,initial,requests,checkpoints,calls,after:hex(state.bytes)});}console.log(JSON.stringify(scenes));
"""
    scenes=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;n.load_title([dict(archive='th06IN.dat',file='ascii.anm',slot=1,base=0),dict(archive='th06IN.dat',file='asciis.anm',slot=2,base=0x77)]);calls=[];digest=hashlib.sha256();draws=0
    def normalize(raw):
        raw=bytearray(raw)
        for offset in [0x10,0x130]:
            p=offset+0x100;ptr=struct.unpack_from('<Q',raw,p)[0]
            if ptr:struct.pack_into('<Q',raw,p,(ptr-n.manager-0x608)//64+1)
        return bytes(raw)
    def hook(m,a,size,u):
        if a==0x1402bdee2:m.mem_write(m.reg_read(UC_X86_REG_RCX),bytes([m.reg_read(UC_X86_REG_RDX)&255])*m.reg_read(UC_X86_REG_R8))
        elif a==0x140002a80:
            raw=normalize(bytes(m.mem_read(n.owner,0xdbb8)));calls.append(dict(kind='draw',state=raw[0x10:0x130].hex()))
        else:calls.append(dict(kind='camera',minZ=struct.unpack('<f',struct.pack('<I',m.reg_read(UC_X86_REG_XMM1)&0xffffffff))[0],maxZ=struct.unpack('<f',struct.pack('<I',m.reg_read(UC_X86_REG_XMM2)&0xffffffff))[0],perspective=a==0x14007af40))
        sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x1402bdee2,0x140002a80,0x14007af40,0x14007b120]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    def run(a):
        sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.emu_start(a,n.stack+0xf000,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000
    for index,s in enumerate(scenes):
        m.mem_write(n.owner,bytes(0xdbb8));run(0x140009790);assert normalize(bytes(m.mem_read(n.owner,0xdbb8))).hex()==s['initial'],(index,'init');m.mem_write(n.owner+0x7bb0,struct.pack('<i',s['cursor']))
        for k,(r,c)in enumerate(zip(s['requests'],s['checkpoints'])):
            m.mem_write(n.owner,struct.pack('<2f',*r['scale']));m.mem_write(n.owner+0x52cc,struct.pack('<I',r['color']));m.mem_write(n.owner+0x52c8,bytes([r['camera'],r['alternate']]));m.mem_write(n.vm,struct.pack('<3f',*r['position']));sp=n.stack+0x8000;m.mem_write(sp+0x30,r['text'].encode('latin-1')+b'\0');m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RDI,n.owner);m.reg_write(UC_X86_REG_RSI,n.vm);m.emu_start(0x140009b07,0x140009ba5,count=1000000);actual=normalize(bytes(m.mem_read(n.owner,0xdbb8)));assert actual.hex()==c['state'],(index,k,'enqueue');digest.update(actual)
        calls.clear();run(0x140009890);actual=normalize(bytes(m.mem_read(n.owner,0xdbb8)));assert actual.hex()==s['after'],(index,'after');assert calls==s['calls'],(index,'calls',calls[:2],s['calls'][:2]);digest.update(actual);draws+=sum(c['kind']=='draw'for c in calls)
    assert {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}==hashes;report=dict(scope=__doc__,scenes=len(scenes),enqueueCheckpoints=len(scenes)*4,drawRequests=draws,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-ascii-text-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()

