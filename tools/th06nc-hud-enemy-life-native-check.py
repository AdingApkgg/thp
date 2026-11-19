"""Front loop 3fcf6..3ff48, enemy-life enter/exit/fade and smoothing.

Real front ANMs, complete HUD owner and task header across dialogs, active
toggles, abnormal opacity/target boundaries and both smoothing directions.
Gauge drawing, ECL segment resolution, GPU and full gameplay excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/'+s+'.mjs'for s in ['hud-enemy-life','hud-stock','message-state','anm-vm','anm-rebind']];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
    script="""
import{readFileSync}from'node:fs';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{MessageState}from'./shared/th06nc/message-state.mjs';import{initializeHudFront}from'./shared/th06nc/hud-stock.mjs';import{initializeEnemyLifeHud,advanceHudFront}from'./shared/th06nc/hud-enemy-life.mjs';const F=Math.fround,hex=b=>Buffer.from(b).toString('hex'),bank=new AnmBank();bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/th06CM.dat/front.anm')),0x620,{slot:13});const scenes=[];
function input(frame,pattern){return {active:pattern===0||pattern===1&&frame<90||pattern===2&&frame>=60&&frame<180||pattern===3&&(frame%60)<30,lifeFraction:F([1,.25,-.5,1.5,0][Math.floor(frame/40)%5]),dialog:pattern===3&&frame%70<20?3:-1};}
function header(state,boss){const b=new Uint8Array(0x54),v=new DataView(b.buffer),life=state.hudEnemyLife;v.setFloat32(4,boss.lifeFraction,true);v.setFloat32(8,life.smoothedFraction,true);v.setFloat32(12,.75,true);life.segments.forEach((x,i)=>v.setFloat32(0x10+i*4,x,true));v.setBigUint64(0x38,1n,true);v.setInt32(0x40,life.opacity,true);v.setUint8(0x44,Number(boss.active));return hex(b);}
for(const mode of [0,1,2,3])for(const opacity of [0,3,255])for(const smoothed of [-.1,.5,1.5])for(const pattern of [0,1,2,3]){const state=new MessageState({uniqueScripts:[]},{anmBank:bank,storage:new Uint8Array(0x4228)});initializeHudFront(state);initializeEnemyLifeHud(state);Object.assign(state.hudEnemyLife,{smoothedFraction:F(smoothed),opacity,segments:[F(.1),F(.2),F(.3)]});state.v.setUint8(0x3ec0,mode);const first=input(0,pattern),before=hex(state.bytes),beforeHeader=header(state,first),frames=[];for(let frame=1;frame<=240;frame++){const boss=input(frame,pattern);state.v.setInt32(0x36b0,boss.dialog,true);advanceHudFront(state,boss);if([1,2,15,30,60,90,120,150,180,240].includes(frame))frames.push({frame,state:hex(state.bytes),header:header(state,boss)});}scenes.push({mode,opacity,smoothed,pattern,before,beforeHeader,frames});}console.log(JSON.stringify(scenes));
"""
    scenes=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;n.load_title([dict(archive='th06CM.dat',file='front.anm',slot=13,base=0x620)]);digest=hashlib.sha256();checked=0
    def normalize(raw,reverse=False):
        raw=bytearray(raw)
        for offset in range(0xcc0,0x31e0,0x120):
            for field in [0xf0,0xf8]:
                p=offset+field;ptr=struct.unpack_from('<Q',raw,p)[0]
                if ptr:struct.pack_into('<Q',raw,p,ptr+n.assets if reverse else ptr-n.assets)
            p=offset+0x100;ptr=struct.unpack_from('<Q',raw,p)[0]
            if ptr:struct.pack_into('<Q',raw,p,n.manager+0x608+(ptr-1)*64 if reverse else(ptr-n.manager-0x608)//64+1)
        return bytes(raw)
    def inp(frame,pattern):return (pattern==0 or pattern==1 and frame<90 or pattern==2 and frame>=60 and frame<180 or pattern==3 and frame%60<30,[1,.25,-.5,1.5,0][frame//40%5],3 if pattern==3 and frame%70<20 else-1)
    for index,s in enumerate(scenes):
        m.mem_write(n.owner,normalize(bytes.fromhex(s['before']),True));header=bytearray.fromhex(s['beforeHeader']);struct.pack_into('<Q',header,0x38,n.owner);m.mem_write(n.vm,bytes(header));byFrame={c['frame']:c for c in s['frames']}
        for frame in range(1,241):
            active,target,dialog=inp(frame,s['pattern']);m.mem_write(n.vm+4,struct.pack('<f',target));m.mem_write(n.vm+0x44,bytes([active]));m.mem_write(n.owner+0x36b0,struct.pack('<i',dialog));m.reg_write(UC_X86_REG_RBX,n.vm);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x14003fcf6,0x14003ff48,count=1000000)
            if frame not in byFrame:continue
            c=byFrame[frame];actual=normalize(bytes(m.mem_read(n.owner,0x4228)));assert actual.hex()==c['state'],(index,frame,'owner',[(hex(p),a,b)for p,(a,b)in enumerate(zip(actual,bytes.fromhex(c['state'])))if a!=b][:16]);header=bytearray(m.mem_read(n.vm,0x54));struct.pack_into('<Q',header,0x38,1);assert header.hex()==c['header'],(index,frame,'header',header.hex(),c['header']);digest.update(actual);digest.update(header);checked+=1
    assert {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}==hashes;report=dict(scope=__doc__,scenes=len(scenes),frames=len(scenes)*240,checkpoints=checked,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-hud-enemy-life-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
