"""Complete enemy-life HUD draw prefix 40670..40b0e with actual ECL queries.

Seven original programs, real front ANMs, full HUD/task header, segment-copy
VMs, UCRT text formatting/color and countdown sound queue. Controlled boss
contexts cover dirty/inactive/dialog/fade/countdown branches; GPU excluded.
"""
import ctypes,hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/'+s+'.mjs'for s in ['hud-enemy-life-draw','hud-enemy-life','ecl-life-query','message-state','anm-vm','sound-queue']];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
    script="""
import{readFileSync}from'node:fs';import{readAnm}from'./shared/th06nc/anm.mjs';import{readEcl}from'./shared/th06nc/ecl.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{MessageState}from'./shared/th06nc/message-state.mjs';import{initializeHudFront}from'./shared/th06nc/hud-stock.mjs';import{initializeEnemyLifeHud}from'./shared/th06nc/hud-enemy-life.mjs';import{drawEnemyLifeHud}from'./shared/th06nc/hud-enemy-life-draw.mjs';const F=Math.fround,hex=b=>Buffer.from(b).toString('hex'),bank=new AnmBank();bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/th06CM.dat/front.anm')),0x620,{slot:13});
function header(state,boss,chapter){const b=new Uint8Array(0x54),v=new DataView(b.buffer),life=state.hudEnemyLife;v.setInt32(0,chapter,true);v.setFloat32(4,boss.lifeFraction,true);v.setFloat32(8,life.smoothedFraction,true);v.setFloat32(12,boss.segmentFraction,true);life.segments.forEach((x,i)=>v.setFloat32(0x10+i*4,x,true));v.setUint8(0x1c,Number(boss.dirty));v.setBigUint64(0x38,1n,true);v.setInt32(0x40,life.opacity,true);v.setUint8(0x44,Number(boss.active));v.setInt32(0x4c,boss.remainingSeconds,true);v.setInt32(0x50,life.lastSeconds,true);return hex(b);}
const programs=[];for(let stage=1;stage<=7;stage++){const file='ecldata'+stage+'.ecl',program=readEcl(readFileSync('runtimes/th06nc/artifacts/scripts/th06ST.dat/'+file)),cases=[],roots=[...new Set([0,Math.floor(program.subroutines.length/2),program.subroutines.length-1,...[93,114].map(op=>program.subroutines.findIndex(s=>s.instructions.some(i=>i.opcode===op))).filter(i=>i>=0)])];for(const sub of roots)for(let variant=0;variant<32;variant++){
 const state=new MessageState({uniqueScripts:[]},{anmBank:bank,storage:new Uint8Array(0x4228)});initializeHudFront(state);initializeEnemyLifeHud(state);state.v.setUint8(0x3ec0,variant%4);state.v.setInt32(0x36b0,variant&16?3:-1,true);Object.assign(state.hudEnemyLife,{smoothedFraction:F([.25,1,1.5][variant%3]),opacity:[0,128,255,-1][variant%4],segments:[1,F(.75),F(.25)],lastSeconds:[0,4,9,100][variant%4]});const boss={active:Boolean(variant&4),dirty:Boolean(variant&8),lifeFraction:F(.75),segmentFraction:F(.25),remainingSeconds:[-2,0,4,5,9,10,20,100][variant%8]},entryBytes=new Uint8Array(0x10b0),v=new DataView(entryBytes.buffer),route=program.subroutines[sub],callback=route.instructions.find(i=>i.opcode===114),next=callback?new DataView(callback.args.buffer,callback.args.byteOffset,callback.args.byteLength).getInt32(0,true):sub,pc=route.instructions[Math.floor(route.instructions.length/2)]?.offset??route.offset;v.setUint16(0x80,sub,true);v.setBigUint64(0x88,BigInt(pc),true);v.setInt32(0xa0,5000,true);v.setInt32(0xa4,next,true);v.setInt32(0x238,variant%8===7?0:10000,true);const entry=variant%5===0?null:{v},availableProgram=variant%7===0?null:program,chapter=sub%4+2,spellCounter=variant&2?1:0,sounds=[[-1,-1,-1],[29,7,-1],[1,2,3],[-1,29,-1]][variant%4].slice(),initialSound=[...sounds],soundDisabled=(variant+stage)%3===0,before=hex(state.bytes),beforeHeader=header(state,boss,chapter),calls=[];
 drawEnemyLifeHud(state,boss,(vm,r)=>calls.push({kind:'draw',offset:r.offset,state:hex(vm.state)}),{entry,program:availableProgram,difficulty:variant%5,spellCounter,chapter,soundSlots:sounds,soundDisabled,drawNumber:r=>calls.push({kind:'number',...r})});cases.push({sub,variant,difficulty:variant%5,entry:entry?hex(entryBytes):null,programPresent:Boolean(availableProgram),spellCounter,initialSound,soundDisabled,before,beforeHeader,after:hex(state.bytes),afterHeader:header(state,boss,chapter),calls,sounds});}programs.push({file,cases});}console.log(JSON.stringify(programs));
"""
    programs=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;n.load_title([dict(archive='th06CM.dat',file='front.anm',slot=13,base=0x620)]);calls=[];digest=hashlib.sha256();checked=0;draws=0;crt=ctypes.CDLL('ucrtbase');formatter=crt.__stdio_common_vsprintf;formatter.restype=ctypes.c_int;formatter.argtypes=[ctypes.c_uint64,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_char_p,ctypes.c_void_p,ctypes.c_void_p]
    def normalize(raw,reverse=False):
        raw=bytearray(raw)
        for offset in [*range(0xcc0,0x31e0,0x120),0x3ec8]:
            for field in [0xf0,0xf8]:
                p=offset+field;ptr=struct.unpack_from('<Q',raw,p)[0]
                if ptr:struct.pack_into('<Q',raw,p,ptr+n.assets if reverse else ptr-n.assets)
            p=offset+0x100;ptr=struct.unpack_from('<Q',raw,p)[0]
            if ptr:struct.pack_into('<Q',raw,p,n.manager+0x608+(ptr-1)*64 if reverse else(ptr-n.manager-0x608)//64+1)
        return bytes(raw)
    def hook(m,a,size,u):
        sp=m.reg_read(UC_X86_REG_RSP)
        if a==0x1402bdee2:m.mem_write(m.reg_read(UC_X86_REG_RCX),bytes([m.reg_read(UC_X86_REG_RDX)&255])*m.reg_read(UC_X86_REG_R8))
        elif a==0x140002a80:
            ptr=m.reg_read(UC_X86_REG_RDX);assert m.reg_read(UC_X86_REG_R8)&255==255 and m.reg_read(UC_X86_REG_R9)&255==255 and bytes(m.mem_read(sp+0x28,1))==b'\1';raw=normalize(bytes(m.mem_read(n.owner,0x4228)));calls.append(dict(kind='draw',offset=ptr-n.owner,state=raw[ptr-n.owner:ptr-n.owner+288].hex()))
        elif a==0x140009aa0:
            fmt=bytes(m.mem_read(m.reg_read(UC_X86_REG_R8),16)).split(b'\0')[0].decode();assert fmt in ['%d','%.2d'];value=m.reg_read(UC_X86_REG_R9D);value-=0x100000000 if value&0x80000000 else 0;out=ctypes.create_string_buffer(80);argument=ctypes.c_uint64(value&0xffffffffffffffff);assert formatter(1,out,80,fmt.encode(),None,ctypes.byref(argument))>0;calls.append(dict(kind='number',format=fmt,value=str(value),text=out.value.decode(),position=list(struct.unpack('<3f',m.mem_read(m.reg_read(UC_X86_REG_RDX),12))),color=struct.unpack('<I',m.mem_read(0x1403e38ec,4))[0]))
        m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x140002a80,0x140009aa0,0x1402bdee2,0x1402bcf20]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    programBase=n.assets+0x80000;enemyBase=n.owner+0x10000
    for p in programs:
        m.mem_write(programBase,(ROOT/'runtimes/th06nc/artifacts/scripts/th06ST.dat'/p['file']).read_bytes())
        for index,c in enumerate(p['cases']):
            m.mem_write(n.owner,normalize(bytes.fromhex(c['before']),True));header=bytearray.fromhex(c['beforeHeader']);struct.pack_into('<Q',header,0x38,n.owner);m.mem_write(n.vm,bytes(header));m.mem_write(0x140badf78,struct.pack('<Q',enemyBase if c['entry']else 0))
            if c['entry']:
                enemy=bytearray.fromhex(c['entry']);pc=struct.unpack_from('<Q',enemy,0x88)[0];struct.pack_into('<Q',enemy,0x88,programBase+pc);m.mem_write(enemyBase,bytes(enemy))
            m.mem_write(0x140a6eb78,struct.pack('<Q',programBase if c['programPresent']else 0));m.mem_write(0x1404f27c0,struct.pack('<i',c['difficulty']));m.mem_write(0x140badf60,struct.pack('<i',c['spellCounter']));m.mem_write(0x140509670,struct.pack('<3i',*c['initialSound']));m.mem_write(0x140509694,bytes([c['soundDisabled']]));m.mem_write(0x1403e38ec,struct.pack('<I',0xffffffff));m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.reg_write(UC_X86_REG_RCX,n.vm);calls.clear();m.emu_start(0x140040670,0x140040b0e,count=3000000);assert m.reg_read(UC_X86_REG_RIP)==0x140040b0e
            actual=normalize(bytes(m.mem_read(n.owner,0x4228)));assert actual.hex()==c['after'],(p['file'],index,'owner',[(hex(q),a,b)for q,(a,b)in enumerate(zip(actual,bytes.fromhex(c['after'])))if a!=b][:16]);header=bytearray(m.mem_read(n.vm,0x54));struct.pack_into('<Q',header,0x38,1);assert header.hex()==c['afterHeader'],(p['file'],index,'header',header.hex(),c['afterHeader']);assert calls==c['calls'],(p['file'],index,'calls',calls[-2:],c['calls'][-2:]);assert list(struct.unpack('<3i',m.mem_read(0x140509670,12)))==c['sounds'],(p['file'],index,'sounds');assert struct.unpack('<I',m.mem_read(0x1403e38ec,4))[0]==0xffffffff,(p['file'],index,'font color');digest.update(actual);digest.update(header);checked+=1;draws+=len(calls)
    assert {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}==hashes;report=dict(scope=__doc__,programs=len(programs),scenes=checked,drawRequests=draws,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-hud-enemy-life-draw-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
