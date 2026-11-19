"""Game-owner score smoothing/cap, high score and extend block 3a626..3a7bd.

Full owner bytes and sound/refresh globals across ordinary/protected stocks,
signed stock/index boundaries and capped score inputs. Pause/frame/task owner,
record persistence and GPU excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT

def main():
    sources=['shared/th06nc/score-update.mjs','shared/th06nc/sound-queue.mjs'];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
    script="""
import{advanceScore}from'./shared/th06nc/score-update.mjs';const scenes=[],serial=o=>JSON.parse(JSON.stringify(o,(k,v)=>typeof v==='bigint'?String(v):v));let index=0;for(const score of [0n,9n,100n,10000000n,60000000n,1900000000n,10000000000n])for(const displayScore of [0n,9999990n,9999999990n])for(const scoreDisplayStep of [0n,100n,999999n])for(const lifeProtection of [false,true])for(const continueState of [-1,0,4,5]){const initial={score,displayScore,scoreDisplayStep,lifeProtection,continueState,lives:[0,7,8,255][index%4],deathCount:-2,highScore:1000000n,inputFlags:0xbeef,scoreExtendsDisabled:index%5===0},environment={...initial},soundSlots=[[-1,-1,-1],[28,7,-1],[1,2,3],[-1,28,-1]][index%4].slice(),initialSound=[...soundSlots],soundDisabled=Boolean(index%2),frames=[];for(let frame=1;frame<=8;frame++){advanceScore(environment,{soundSlots,soundDisabled});frames.push({frame,environment:serial(environment),sounds:[...soundSlots]});}scenes.push({initial:serial(initial),initialSound,soundDisabled,frames});index++;}console.log(JSON.stringify(scenes));
"""
    scenes=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256();fields={'score':(0x938,'Q'),'displayScore':(0x930,'Q'),'scoreDisplayStep':(0x940,'Q'),'highScore':(0x948,'Q'),'lifeProtection':(0x964,'B'),'continueState':(0xd292,'B'),'lives':(0xd290,'B'),'deathCount':(0,'i'),'scoreExtendsDisabled':(0x955,'B')};checked=0
    for index,s in enumerate(scenes):
        owner=bytearray(0xe000)
        for key,(p,fmt)in fields.items():struct.pack_into('<'+fmt,owner,p,int(s['initial'][key])&255 if fmt=='B'else int(s['initial'][key]))
        m.mem_write(n.owner,bytes(owner));m.mem_write(0x140509670,struct.pack('<3i',*s['initialSound']));m.mem_write(0x140509694,bytes([s['soundDisabled']]));m.mem_write(0x140a6ec18,struct.pack('<I',s['initial']['inputFlags']))
        for c in s['frames']:
            from unicorn.x86_const import UC_X86_REG_RBX,UC_X86_REG_RDI,UC_X86_REG_R14,UC_X86_REG_RSI,UC_X86_REG_RSP
            for reg,value in [(UC_X86_REG_RBX,n.owner),(UC_X86_REG_RDI,0),(UC_X86_REG_R14,0x140000000),(UC_X86_REG_RSI,0x140509670),(UC_X86_REG_RSP,n.stack+0x8000)]:m.reg_write(reg,value)
            m.emu_start(0x14003a626,0x14003a7bd,count=1000000);expected=bytearray(owner)
            for key,(p,fmt)in fields.items():struct.pack_into('<'+fmt,expected,p,int(c['environment'][key])&255 if fmt=='B'else int(c['environment'][key]))
            actual=bytes(m.mem_read(n.owner,len(owner)));assert actual==expected,(index,c['frame'],'owner',[(hex(p),a,b)for p,(a,b)in enumerate(zip(actual,expected))if a!=b][:16]);assert list(struct.unpack('<3i',m.mem_read(0x140509670,12)))==c['sounds'],(index,c['frame'],'sounds');assert struct.unpack('<I',m.mem_read(0x140a6ec18,4))[0]==c['environment']['inputFlags'],(index,c['frame'],'flags');digest.update(actual);checked+=1
    assert {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}==hashes;report=dict(scope=__doc__,scenes=len(scenes),frames=checked,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-score-update-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()

