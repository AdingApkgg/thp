"""Marisa B bomb e7f0 and ebe0: continuous 302-frame update/draw sequences.

Real player ANMs, complete player/item pools and ordered sound/screen-effect
requests. Caption publication, priority-14 screen effects and 67f0 GPU draw
are observed service boundaries. Trig boundaries cover fixed returns and independent Python scalar sin/cos
against browser Math sin/cos; original embedded trig/GPU pixels not claimed.
"""
import hashlib,json,struct,subprocess,math
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/'+name+'.mjs'for name in ['player-bomb-marisa-b','anm-initialize','anm-rebind','sprite-layout','sound-queue']];hashes={source:hashlib.sha256((ROOT/source).read_bytes()).hexdigest()for source in sources}
    script="""
import{readFileSync}from'node:fs';import{createHash}from'node:crypto';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{PlayerState}from'./shared/th06nc/player-state.mjs';import{playerAssetPlan}from'./shared/th06nc/player-init.mjs';import{NativeRng}from'./shared/th06nc/rng.mjs';import{updateMarisaBBomb,drawMarisaBBomb}from'./shared/th06nc/player-bomb-marisa-b.mjs';const scenes=[],hex=b=>Buffer.from(b).toString('hex'),hash=b=>createHash('sha256').update(b).digest('hex');
for(const trig of ['fixed','scalar'])for(const soundDisabled of [false,true])for(const initialSound of [[-1,-1,-1],[-1,19,-1],[19,7,-1],[1,2,3]]){
 const ref=playerAssetPlan(1),bank=new AnmBank();bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+ref.archive+'/'+ref.file)),ref.base,{slot:ref.slot});const rng=new NativeRng(0xbeef,99),environment={rng,character:1,shot:1,playerPower:128},player=new PlayerState({anmBank:bank,environment,skipIntro:true}),v=player.v,itemPool={storage:new Uint8Array(1025*0x160)},sounds=[...initialSound],frames=[];for(let slot=0;slot<1025;slot++){itemPool.storage[slot*0x160]=slot%3===0?0:slot%2?1:255;itemPool.storage[slot*0x160+12]=2;}v.setUint8(0x9ec8,1);v.setInt32(0x7ac0,-999,true);v.setInt32(0x7ac4,0,true);v.setInt32(0x9f20,999,true);const initial=hex(player.bytes),initialItems=hex(itemPool.storage);
 for(let frame=1;frame<=302;frame++){
  player.position=[Math.fround(192+frame*.125),Math.fround(384-frame*.25),.49];for(let i=0;i<32;i++)v.setInt32(0x180+i*12,0,true);for(let i=0;i<16;i++)v.setInt32(0x7754+i*16,0,true);const events=[],draws=[];
  if(v.getUint8(0x9ec8))updateMarisaBBomb(player,{itemPool,soundSlots:sounds,soundDisabled,publishBombName:r=>events.push({kind:'caption',...r}),finishBombName:()=>events.push({kind:'finishCaption'}),screenEffect:r=>events.push({kind:'screen',...r})});
  if(v.getUint8(0x9ec8))drawMarisaBBomb(player,(vm,info)=>draws.push({slot:info.slot,state:hex(vm.state)}),trig==='fixed'?{sin:()=>.25,cos:()=>.75}:{});
  if([1,2,3,4,5,60,61,120,121,299,300,301,302].includes(frame))frames.push({frame,state:hex(player.bytes),itemsSha256:hash(itemPool.storage),sounds:[...sounds],events,draws,rng:{seed:rng.seed,count:rng.count}});
 }scenes.push({ref,trig,soundDisabled,initialSound,initial,initialItems,frames});
}console.log(JSON.stringify(scenes));
"""
    scenes=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;events=[];draws=[];digest=hashlib.sha256();checked=0;current={}
    def normalize(data):
        data=bytearray(data)
        for offset in [0x78c8,0x9f38,0xa058,*[0x7ac8+i*288 for i in range(4)]]:
            for field in [0xf0,0xf8]:
                p=offset+field;ptr=struct.unpack_from('<Q',data,p)[0]
                if ptr:struct.pack_into('<Q',data,p,ptr-n.assets)
            p=offset+0x100;ptr=struct.unpack_from('<Q',data,p)[0]
            if ptr:struct.pack_into('<Q',data,p,(ptr-n.manager-0x608)//64+1)
        return bytes(data)
    def hook(m,a,size,u):
        if a==0x14000e89c:
            events.append(dict(kind='caption',key='EXE_MARISA_B_BOMB_NAME',resourceSlot=16));m.reg_write(UC_X86_REG_ESI,0);m.reg_write(UC_X86_REG_RIP,0x14000e981);return
        if a==0x14000e807:events.append(dict(kind='finishCaption'));return
        if a==0x1400760f0:events.append(dict(kind='screen',frames=m.reg_read(UC_X86_REG_EDX),amplitude=m.reg_read(UC_X86_REG_R8D),endAmplitude=m.reg_read(UC_X86_REG_R9D)))
        elif a==0x1400067f0:
            ptr=m.reg_read(UC_X86_REG_RDX);slot=(ptr-n.owner-0x7ac8)//288;state=normalize(bytes(m.mem_read(n.owner,0xa2b8)))[0x7ac8+slot*288:0x7ac8+(slot+1)*288];draws.append(dict(slot=slot,state=state.hex()))
        else:
            angle=struct.unpack('<f',struct.pack('<I',m.reg_read(UC_X86_REG_XMM0)&0xffffffff))[0];value=(.75 if a==0x1402be071 else .25)if current['trig']=='fixed'else(math.cos(angle)if a==0x1402be071 else math.sin(angle));m.reg_write(UC_X86_REG_XMM0,int.from_bytes(struct.pack('<f',value),'little'))
        sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x14000e89c,0x14000e807,0x1400760f0,0x1400067f0,0x1402be071,0x1402be07d]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    def run(address):
        sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.emu_start(address,n.stack+0xf000,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000
    for sceneIndex,s in enumerate(scenes):
        current=s;n.load_title([s['ref']]);initial=bytearray.fromhex(s['initial'])
        for offset in [0x78c8,0x9f38,0xa058]:
            for field in [0xf0,0xf8]:
                p=offset+field;ptr=struct.unpack_from('<Q',initial,p)[0]
                if ptr:struct.pack_into('<Q',initial,p,ptr+n.assets)
            p=offset+0x100;ptr=struct.unpack_from('<Q',initial,p)[0]
            if ptr:struct.pack_into('<Q',initial,p,n.manager+0x608+(ptr-1)*64)
        m.mem_write(n.owner,bytes(initial));m.mem_write(0x140baf0d8,bytes.fromhex(s['initialItems']));m.mem_write(0x140a6ec08,struct.pack('<Q',n.vm));m.mem_write(0x140509670,struct.pack('<3i',*s['initialSound']));m.mem_write(0x140509694,bytes([s['soundDisabled']]));m.mem_write(0x140a6ec40,struct.pack('<IH',99,0xbeef));byFrame={c['frame']:c for c in s['frames']}
        for frame in range(1,303):
            m.mem_write(n.owner+0x7730,struct.pack('<3f',192+frame*.125,384-frame*.25,.49))
            for i in range(32):m.mem_write(n.owner+0x180+i*12,bytes(4))
            for i in range(16):m.mem_write(n.owner+0x7754+i*16,bytes(4))
            events.clear();draws.clear()
            if m.mem_read(n.owner+0x9ec8,1)[0]:run(0x14000e7f0)
            if m.mem_read(n.owner+0x9ec8,1)[0]:run(0x14000ebe0)
            if frame not in byFrame:continue
            c=byFrame[frame];actual=normalize(bytes(m.mem_read(n.owner,0xa2b8)));wanted=bytes.fromhex(c['state']);assert actual==wanted,(sceneIndex,frame,[(hex(p),a,b)for p,(a,b)in enumerate(zip(actual,wanted))if a!=b][:30]);assert events==c['events'],(sceneIndex,frame,events,c['events']);assert draws==c['draws'],(sceneIndex,frame,'draws');assert list(struct.unpack('<3i',m.mem_read(0x140509670,12)))==c['sounds'];assert hashlib.sha256(m.mem_read(0x140baf0d8,1025*0x160)).hexdigest()==c['itemsSha256'];count,seed=struct.unpack('<IH',m.mem_read(0x140a6ec40,6));assert dict(seed=seed,count=count)==c['rng'];digest.update(actual);checked+=1
    assert {source:hashlib.sha256((ROOT/source).read_bytes()).hexdigest()for source in sources}==hashes
    report=dict(scope=__doc__,scenes=len(scenes),frames=len(scenes)*302,checkpoints=checked,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-bomb-marisa-b-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
