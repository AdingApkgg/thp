"""Base ECL timeline phase on all original timeline events and frame boundaries.

Spawn/ECL initialization and message calls are observable services; validates
controller state, RNG, event parameters and mirror bits, not complete gameplay.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    script="""
import{readFileSync}from'node:fs';import{readEcl}from'./shared/th06nc/ecl.mjs';import{EclTimeline}from'./shared/th06nc/ecl-timeline.mjs';import{NativeRng}from'./shared/th06nc/rng.mjs';import{createEnemyTemplate}from'./shared/th06nc/enemy-pool.mjs';
const cases=[],files=JSON.parse(readFileSync('artifacts/th06nc/scripts.json')).filter(f=>f.name.endsWith('.ecl')),bits=position=>{const b=Buffer.alloc(12);position.forEach((x,i)=>b.writeFloatLE(x,i*4));return b.toString('hex');};
for(const [fileIndex,file]of files.entries()){
const timeline=readEcl(readFileSync(file.path)).timelines[0];
for(const ins of timeline.instructions)for(const delta of [-1,0,1])for(const variant of ins.opcode>=8?[0,1,2]:[0])for(const suppressSpawn of [false,true]){
const rng=new NativeRng(0xbeef,99),events=[],actors=[],slots=Array.from({length:8},()=>{const enemy=new Uint8Array(0x10b0);return{v:new DataView(enemy.buffer)};}),environment={rng,difficulty:variant===2?0:1,stageIndex:fileIndex,character:variant===1?1:0,suppressSpawn,messageField3b50:variant===1?1:0,messageField36b0:variant===2?-1:0};if(variant===1)for(const slot of slots)slot.v.setUint8(0xbc,128);
const controller=new EclTimeline(timeline,{environment,bossSlots:slots,spawn:args=>{events.push({kind:'spawn',...args,position:bits(args.position)});const enemy=createEnemyTemplate(),entry={v:new DataView(enemy.buffer)};actors.push(entry);return entry;},openMessage:id=>events.push({kind:'message',id})});controller.cursor=ins.offset;controller.frame=ins.time+delta;controller.parameterWord=0xabcd;controller.messageMode=0x1234;controller.messageClock=7;const initial={cursor:controller.cursor,frame:controller.frame};controller.runDue();cases.push({fileIndex,initial,environment:{...environment,rng:undefined},events,actors:actors.map(a=>a.v.getUint8(0xbc)),slotValues:slots.map(s=>s.v.getInt32(0xf70,true)),slotActive:slots.map(s=>s.v.getUint8(0xbc)),state:{cursor:controller.cursor,frame:controller.frame,parameterWord:controller.parameterWord,messageMode:controller.messageMode,messageClock:controller.messageClock},rng:{seed:rng.seed,count:rng.count}});
}}
console.log(JSON.stringify({files,template:Buffer.from(createEnemyTemplate()).toString('hex'),cases}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;owner=0x140aa1e90;template=bytes.fromhex(data['template']);programBase=n.assets;events=[];actorPointers=[];current=None;digest=hashlib.sha256()
    for i in range(1024):m.mem_write(n.vm+0x8000+i*8,struct.pack('<Q',n.assets+0x100000))
    m.mem_write(0x140a6eb80,struct.pack('<Q',n.vm+0x8000));m.mem_write(0x140a6ec08,struct.pack('<Q',n.owner));m.mem_write(0x1404ff0e8,struct.pack('<2f',384,448))
    def signed16(x):return struct.unpack('<h',struct.pack('<H',x&65535))[0]
    def spawn_event(sub,position,life,item,score):events.append(dict(kind='spawn',sub=sub,position=position,life=life,item=item,score=score))
    def hook(m,a,size,u):
        sp=m.reg_read(UC_X86_REG_RSP)
        if a==0x1400360d0:
            sub=m.reg_read(UC_X86_REG_RDX)&0xffffffff;sub=sub if sub<0x80000000 else sub-0x100000000;position=bytes(m.mem_read(m.reg_read(UC_X86_REG_R8),12)).hex();life=signed16(m.reg_read(UC_X86_REG_R9));item=signed16(struct.unpack('<H',m.mem_read(sp+0x28,2))[0]);score=struct.unpack('<i',m.mem_read(sp+0x30,4))[0]
            spawn_event(sub,position,life if life<0 else life&65535,item if item<0 else item&65535,score);ptr=owner+8+len(actorPointers)*0x10b0;actorPointers.append(ptr);m.mem_write(ptr,template);m.reg_write(UC_X86_REG_RAX,ptr)
        elif a==0x140022060:
            ptr=m.reg_read(UC_X86_REG_RDX);spawn_event(struct.unpack('<h',m.mem_read(ptr+0x80,2))[0],bytes(m.mem_read(ptr+0xb0,12)).hex(),-1,-1,-1);actorPointers.append(ptr);m.reg_write(UC_X86_REG_RAX,0)
        elif a==0x14003ece0:events.append(dict(kind='message',id=m.reg_read(UC_X86_REG_RDX)&0xffffffff));m.reg_write(UC_X86_REG_RAX,0)
        elif a==0x1402bdee8:
            dst=m.reg_read(UC_X86_REG_RCX);src=m.reg_read(UC_X86_REG_RDX);size=m.reg_read(UC_X86_REG_R8);m.mem_write(dst,bytes(m.mem_read(src,size)));m.reg_write(UC_X86_REG_RAX,dst)
        else:return
        m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    m.hook_add(UC_HOOK_CODE,hook)
    for index,c in enumerate(data['cases']):
        if current!=c['fileIndex']:current=c['fileIndex'];m.mem_write(programBase,open(data['files'][current]['path'],'rb').read())
        m.mem_write(owner,bytes(0x10d1e0));m.mem_write(owner+0x10c130,template);m.mem_write(owner+0x10c128,struct.pack('<Q',programBase+c['initial']['cursor']));m.mem_write(owner+0x10c0bc,struct.pack('<i',c['initial']['frame']));m.mem_write(0x140a6eb90,b'\0');m.mem_write(0x140a6ec14,bytes([c['environment']['suppressSpawn']]));m.mem_write(0x140a6ec40,struct.pack('<IH',99,0xbeef));env=c['environment'];m.mem_write(0x1404f27c0,struct.pack('<i',env['difficulty']));m.mem_write(0x1404f1e84,struct.pack('<i',env['stageIndex']));m.mem_write(0x1404f1e80,bytes([env['character']]));m.mem_write(n.owner+0x3b50,struct.pack('<I',env['messageField3b50']));m.mem_write(n.owner+0x36b0,struct.pack('<i',env['messageField36b0']));m.mem_write(0x1404f1e88,struct.pack('<H',0xabcd));m.mem_write(0x140c21974,struct.pack('<i',0x1234));m.mem_write(0x1404ff0d8,struct.pack('<i',7))
        for slot in range(8):
            ptr=n.owner+0x4000+slot*0x1100;m.mem_write(ptr,bytes(0x10b0));m.mem_write(ptr+0xbc,bytes([c['slotActive'][slot]]));m.mem_write(owner+0x10c0e8+slot*8,struct.pack('<Q',ptr))
        events.clear();actorPointers.clear()
        for reg,value in [(UC_X86_REG_RSP,n.stack+0x8000),(UC_X86_REG_RDI,owner),(UC_X86_REG_RCX,owner)]:m.reg_write(reg,value)
        m.emu_start(0x1400363c2,0x140036ec7,count=1000000)
        assert events==c['events'],(index,c['fileIndex'],c['initial'],events,c['events'])
        actors=[m.mem_read(p+0xbc,1)[0]for p in actorPointers];assert actors==c['actors'],(index,actors,c['actors'])
        actual=dict(cursor=struct.unpack('<Q',m.mem_read(owner+0x10c128,8))[0]-programBase,frame=struct.unpack('<i',m.mem_read(owner+0x10c0bc,4))[0],parameterWord=struct.unpack('<H',m.mem_read(0x1404f1e88,2))[0],messageMode=struct.unpack('<i',m.mem_read(0x140c21974,4))[0],messageClock=struct.unpack('<i',m.mem_read(0x1404ff0d8,4))[0]);assert actual==c['state'],(index,actual,c['state'])
        values=[struct.unpack('<i',m.mem_read(n.owner+0x4000+s*0x1100+0xf70,4))[0]for s in range(8)];assert values==c['slotValues'],index
        count,seed=struct.unpack('<IH',m.mem_read(0x140a6ec40,6));assert dict(seed=seed,count=count)==c['rng'],index;digest.update(json.dumps(dict(state=actual,events=events,actors=actors),sort_keys=True).encode())
    report=dict(scope=__doc__,cases=len(data['cases']),events=sum(len(c['events'])for c in data['cases']),stateSha256=digest.hexdigest(),sourceSha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in ['shared/th06nc/ecl-timeline.mjs','shared/th06nc/rng.mjs']},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-ecl-timeline-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
