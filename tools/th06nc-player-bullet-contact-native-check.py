"""Actual ordinary bullet/player contact helper: circle/rectangle hits and cancellation.

Whole original helper executes with observed effect calls and shared trig values.
Player movement/death lifecycle, effect simulation and GPU are excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    script="""
import{collidePlayerWithBullet}from'./shared/th06nc/player-bullet-contact.mjs';const cases=[];
for(const dx of [-100,-61,-60,-59,-14,-13,-12,0,12,13,14,59,60,61,100])for(const dy of [0,5,55])for(const radius of [0,3])for(const state of [0,1,2,3,255])for(const graze of [false,true])for(const angle of [0,0.5]){
 const index=cases.length,player={position:[120+dx,200+dy,0.5],hitRadius:radius,state,deathBombFrames:17,hitTimer:{previous:7,frame:8},hitAnimationTimers:[{previous:9,frame:10},{previous:11,frame:12}]},environment={spellActive:true,grazeCountersDisabled:index%3===0,stageGraze:[0,99998,99999,2147483647][index%4],totalGraze:[0,999998,999999,2147483647][index%4],score:18446744073709551610n,inputFlags:255},query={position:[120,200,0],size:[20,8,0],circle:graze},soundDisabled=index%7===0,soundSlots=[[-1,-1,-1],[4,-1,-1],[30,-1,-1],[1,2,3]][index%4].slice(),events=[],sin=Math.fround(Math.sin(angle)),cos=Math.fround(Math.cos(angle)),initial={player:structuredClone(player),environment:{...environment,score:String(environment.score)},soundSlots:[...soundSlots]};
 const result=collidePlayerWithBullet(query,{player,environment,soundSlots,soundDisabled,spawnEffect:e=>events.push(e),queryCancel:()=>index%5===0});cases.push({query,initial,soundDisabled,cancel:index%5===0,sin,cos,result,player,environment:{...environment,score:String(environment.score)},soundSlots,events});
}console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;current=None;events=[];digest=hashlib.sha256()
    def hook(m,a,size,u):
        sp=m.reg_read(UC_X86_REG_RSP)
        if a==0x14002b0d0:events.append(dict(type=m.reg_read(UC_X86_REG_EDX),count=m.reg_read(UC_X86_REG_R9D),color=struct.unpack('<I',m.mem_read(sp+0x28,4))[0],position=list(struct.unpack('<3f',m.mem_read(m.reg_read(UC_X86_REG_R8),12)))));m.reg_write(UC_X86_REG_RAX,0)
        else:m.reg_write(UC_X86_REG_RAX,1 if current['cancel'] else 0)
        m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for address in [0x14006a8c0,0x14002b0d0]:m.hook_add(UC_HOOK_CODE,hook,begin=address,end=address)
    for index,c in enumerate(cases):
        current=c;p=c['initial']['player'];env=c['initial']['environment'];q=c['query'];m.mem_write(0x140506ad0,struct.pack('<3f',*p['position']));m.mem_write(0x140506aec,struct.pack('<f',p['hitRadius']));m.mem_write(0x140506c38,bytes([p['state']]));m.mem_write(0x140506adc,struct.pack('<i',p['deathBombFrames']));m.mem_write(0x140506bf4,struct.pack('<2i',p['hitTimer']['previous'],p['hitTimer']['frame']));m.mem_write(0x140506d88,struct.pack('<4i',p['hitAnimationTimers'][0]['previous'],p['hitAnimationTimers'][0]['frame'],p['hitAnimationTimers'][1]['previous'],p['hitAnimationTimers'][1]['frame']));m.mem_write(0x140badf6c,bytes([env['spellActive']]));m.mem_write(0x140509268,bytes([env['grazeCountersDisabled']]));m.mem_write(0x1404ff0cc,struct.pack('<2i',env['stageGraze'],env['totalGraze']));m.mem_write(0x1404f2798,struct.pack('<Q',int(env['score'])));m.mem_write(0x140a6ec18,struct.pack('<I',env['inputFlags']));m.mem_write(0x140509670,struct.pack('<3i',*c['initial']['soundSlots']));m.mem_write(0x140509694,bytes([c['soundDisabled']]));m.mem_write(n.vm,struct.pack('<2f',*q['position'][:2]));m.mem_write(n.vm+16,struct.pack('<3f',*q['size']));sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));
        for reg,value in [(UC_X86_REG_RSP,sp),(UC_X86_REG_RCX,0x1404ff3a0),(UC_X86_REG_RDX,n.vm),(UC_X86_REG_R8,n.vm+16),(UC_X86_REG_R9,int(q['circle']))]:m.reg_write(reg,value)
        events.clear();m.emu_start(0x14006a980,n.stack+0xf000,count=100000);assert m.reg_read(UC_X86_REG_EAX)==c['result'],(index,'result');assert events==c['events'],(index,'effects',events,c['events']);p=c['player'];env=c['environment'];assert m.mem_read(0x140506c38,1)[0]==p['state'],(index,'state');assert struct.unpack('<i',m.mem_read(0x140506adc,4))[0]==p['deathBombFrames'],(index,'deathbomb');assert struct.unpack('<2i',m.mem_read(0x140506bf4,8))==(p['hitTimer']['previous'],p['hitTimer']['frame']),(index,'hit timer');assert struct.unpack('<4i',m.mem_read(0x140506d88,16))==tuple(x for t in p['hitAnimationTimers']for x in [t['previous'],t['frame']]),(index,'animation timers')
        assert bool(m.mem_read(0x140badf6c,1)[0])==env['spellActive'],(index,'spell');assert struct.unpack('<2i',m.mem_read(0x1404ff0cc,8))==(env['stageGraze'],env['totalGraze']),(index,'graze counters');assert str(struct.unpack('<Q',m.mem_read(0x1404f2798,8))[0])==env['score'],(index,'score');assert struct.unpack('<I',m.mem_read(0x140a6ec18,4))[0]==env['inputFlags'],(index,'input flags');assert list(struct.unpack('<3i',m.mem_read(0x140509670,12)))==c['soundSlots'],(index,'sound');digest.update(json.dumps(dict(result=c['result'],player=p,environment=env,events=events),sort_keys=True).encode())
    report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256=hashlib.sha256((ROOT/'shared/th06nc/player-bullet-contact.mjs').read_bytes()).hexdigest(),executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-player-bullet-contact-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
