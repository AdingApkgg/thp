"""Common message commands against their original 3eee0 dispatch branches.

Every original supported command, real portrait ANM, text publication arguments,
wait gates and message fields compared. Localization lookup/text textures are
controlled services. Music, stage transitions, special ending commands excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/message-state.mjs','shared/th06nc/message-command.mjs'];hashes={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources}
    script="""
import{readFileSync}from'node:fs';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{readMessage}from'./shared/th06nc/message.mjs';import{MessageState}from'./shared/th06nc/message-state.mjs';import{applyMessageCommand}from'./shared/th06nc/message-command.mjs';const refs=[{archive:'th06IN.dat',file:'text.anm',slot:0,base:0x72f},{archive:'th06CM.dat',file:'face00a.anm',slot:12,base:0x4c0},{archive:'th06ST.dat',file:'face03a.anm',slot:14,base:0x4c6}],bank=new AnmBank(),cases=[];for(const r of refs)bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+r.archive+'/'+r.file)),r.base,{slot:r.slot});for(let file=1;file<=7;file++){const program=readMessage(readFileSync('runtimes/th06nc/artifacts/scripts/th06ST.dat/msg'+file+'.dat'));for(const ins of program.uniqueScripts.flatMap(s=>s.instructions).filter(i=>[0,1,2,3,4,5,6,8,10,13].includes(i.opcode)))for(let variant=0;variant<(ins.opcode===4?8:2);variant++){
 const state=new MessageState(program,{anmBank:bank}),{v}=state;v.setInt32(0x36b0,0,true);v.setBigUint64(0x3668,BigInt(ins.offset),true);v.setInt16(0x3810,variant&1?0:-1,true);v.setInt32(0x3420,[7,8,300,0][variant%4],true);v.setUint8(0x3424,15);v.setUint8(0x3900,variant&1);for(const[p,x]of [[0x3670,0xffffff],[0x3674,0xfff0f0],[0x3690,0x10101],[0x3694,0x10101],[0x36a0,0x50505],[0x36a4,0x50505]])v.setUint32(p,x,true);const events=[],input=[0,1,1,0x100,8,8,0x300,0][variant],previousInput=[0,0,1,1,0,8,0,0][variant],action=applyMessageCommand(state,ins,{input,previousInput,publishText:r=>events.push(r)});cases.push({file,offset:ins.offset,opcode:ins.opcode,variant,input,previousInput,action,events,after:Buffer.from(state.bytes.subarray(0x3420,0x3ec8)).toString('hex')});
}}console.log(JSON.stringify({refs,cases}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();n.load_title(data['refs']);m=n.m;programBase=n.assets+0x100000;events=[];action=None;digest=hashlib.sha256()
    starts={0:0x3fbda,1:0x3efe6,2:0x3f084,3:0x3f0c1,4:0x3f404,5:0x3f461,6:0x3f492,8:0x3f6d1,10:0x3f32d,13:0x3fa18}
    def hook(m,a,size,u):
        nonlocal action
        if a in [0x14003f2f0,0x14003f32d,0x14003fc12]:action='advance'if a==0x14003f2f0 else'end'if a==0x14003fc12 else'wait';m.emu_stop();return
        if a in [0x14003f1eb,0x14003f771]:
            m.reg_write(UC_X86_REG_RIP,0x14003f28f if a==0x14003f1eb else 0x14003f80f);return
        sp=m.reg_read(UC_X86_REG_RSP);ptr=m.reg_read(UC_X86_REG_RDX);string=struct.unpack('<Q',m.mem_read(sp+0x38,8))[0];key=bytes(m.mem_read(string,128)).split(b'\0')[0].decode();events.append(dict(offset=ptr-n.owner,key=key,text=key,colors=[m.reg_read(UC_X86_REG_R8D),m.reg_read(UC_X86_REG_R9D),struct.unpack('<I',m.mem_read(sp+0x28,4))[0],struct.unpack('<I',m.mem_read(sp+0x30,4))[0]]));m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x14003f2f0,0x14003f32d,0x14003fc12,0x14003f1eb,0x14003f771,0x140007530]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    current=None
    for index,c in enumerate(data['cases']):
        if current!=c['file']:current=c['file'];m.mem_write(programBase,(ROOT/f'runtimes/th06nc/artifacts/scripts/th06ST.dat/msg{current}.dat').read_bytes())
        initial=bytearray(0x4000);struct.pack_into('<i',initial,0x36b0,0);struct.pack_into('<Q',initial,0x3668,programBase+c['offset']);struct.pack_into('<Q',initial,0x38f8,1);struct.pack_into('<Q',initial,0x3b58,1);struct.pack_into('<h',initial,0x3810,0 if c['variant']&1 else -1);struct.pack_into('<i',initial,0x3420,[7,8,300,0][c['variant']%4]);initial[0x3424]=15;initial[0x3900]=c['variant']&1
        for p,x in [(0x3670,0xffffff),(0x3674,0xfff0f0),(0x3690,0x10101),(0x3694,0x10101),(0x36a0,0x50505),(0x36a4,0x50505)]:struct.pack_into('<I',initial,p,x)
        m.mem_write(n.owner,bytes(initial));m.mem_write(0x140a6ec60,struct.pack('<2I',c['input'],c['previousInput']));events.clear();action=None
        for reg,value in [(UC_X86_REG_RDI,n.owner),(UC_X86_REG_R14,programBase+c['offset']),(UC_X86_REG_R12,0xffffffffffffffff),(UC_X86_REG_RSI,0),(UC_X86_REG_R9D,0x4c0),(UC_X86_REG_R10D,0x648),(UC_X86_REG_R11D,0x730),(UC_X86_REG_R15D,0x731),(UC_X86_REG_RBX,0x14030b170),(UC_X86_REG_R8D,1),(UC_X86_REG_RBP,n.stack+0x8000),(UC_X86_REG_RSP,n.stack+0x7000)]:m.reg_write(reg,value)
        m.emu_start(0x140000000+starts[c['opcode']],n.stack+0xf000,count=1000000);assert action==c['action'],(index,c['opcode'],action,c['action']);assert events==c['events'],(index,c['opcode'],'text',events,c['events']);actual=bytearray(m.mem_read(n.owner,0x4000));struct.pack_into('<Q',actual,0x3668,struct.unpack_from('<Q',actual,0x3668)[0]-programBase)
        for offset in [0x3428,0x3548,0x36b8,0x37d8,0x3910,0x3a30,0x3b60]:
            for field in [0xf0,0xf8]:
                p=offset+field;ptr=struct.unpack_from('<Q',actual,p)[0]
                if ptr:struct.pack_into('<Q',actual,p,ptr-next(a for a,b in n.ranges if a<=ptr<b))
            p=offset+0x100;ptr=struct.unpack_from('<Q',actual,p)[0]
            if ptr:struct.pack_into('<Q',actual,p,(ptr-n.manager-0x608)//64+1)
        actual=actual[0x3420:0x3ec8];wanted=bytes.fromhex(c['after']);assert actual==wanted,(index,c['opcode'],c['variant'],[(hex(0x3420+p),a,b)for p,(a,b)in enumerate(zip(actual,wanted))if a!=b][:30]);digest.update(actual)
    assert hashes=={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources}
    report=dict(scope=__doc__,cases=len(data['cases']),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-message-command-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
