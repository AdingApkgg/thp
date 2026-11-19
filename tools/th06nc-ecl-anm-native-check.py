"""ECL enemy animation binding commands 97/99 with actual ANM setter and tick.

Stage enemy ANMs are loaded at a controlled base/slot. This checks binding,
not the game's complete resource plan, animation lifetime, drawing or gameplay.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *

def main():
    script="""
import{readFileSync}from'node:fs';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{applyEclCommand}from'./shared/th06nc/ecl-command.mjs';
const refs=JSON.parse(readFileSync('artifacts/th06nc/scripts.json')).filter(f=>/^stg[1-7]enm/.test(f.name)).map(f=>({...f,file:f.name,slot:8,base:256})),cases=[];
for(const [resourceIndex,ref]of refs.entries()){
const resource=readAnm(readFileSync(ref.path)),bank=new AnmBank();bank.load(resource,256,{slot:8});
for(const id of [...new Set(resource.scripts.map(s=>s.id)),0x6ff])for(const opcode of [97,99]){
const enemy=new Uint8Array(0x1100),v=new DataView(enemy.buffer);for(let p=0;p<enemy.length;p+=4)v.setFloat32(p,(p%37)-15.75,true);
const offset=opcode===97?0x108:0x2d8+288;for(const p of [0xf0,0xf8,0x100])v.setBigUint64(offset+p,0n,true);
const before=Buffer.from(enemy).toString('hex'),args=Buffer.alloc(opcode===97?4:8);args.writeInt32LE(opcode===97?id:1);if(opcode===99)args.writeInt32LE(id,4);
applyEclCommand(enemy,{opcode,args},{anmBank:bank,enemyAnms:new Map()});cases.push({resourceIndex,id,opcode,offset,args:args.toString('hex'),before,after:Buffer.from(enemy).toString('hex')});}
}
console.log(JSON.stringify({refs,cases}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256();current=None
    for index,c in enumerate(data['cases']):
        if current!=c['resourceIndex']:
            current=c['resourceIndex'];n.load_title([data['refs'][current]])
        raw=bytes.fromhex(c['args']);m.mem_write(n.owner,bytes.fromhex(c['before']));m.mem_write(n.vm,struct.pack('<ihH4B',0,c['opcode'],12+len(raw),0,255,0,0)+raw)
        sp=n.stack+0x8000;m.mem_write(sp+0x48,struct.pack('<Q',n.vm))
        for reg,value in [(UC_X86_REG_RSP,sp),(UC_X86_REG_RBP,n.stack+0x9000),(UC_X86_REG_RDI,n.owner),(UC_X86_REG_RSI,n.vm+12),(UC_X86_REG_R14,n.vm),(UC_X86_REG_R10,0x140000000),(UC_X86_REG_R12,0)]:m.reg_write(reg,value)
        m.emu_start(0x140024ff8 if c['opcode']==97 else 0x14002506a,0x140025d7d,count=100000)
        actual=bytearray(m.mem_read(n.owner,0x1100));offset=c['offset']
        for p in [0xf0,0xf8]:
            ptr=struct.unpack_from('<Q',actual,offset+p)[0]
            if ptr:struct.pack_into('<Q',actual,offset+p,ptr-n.assets)
        ptr=struct.unpack_from('<Q',actual,offset+0x100)[0]
        if ptr:struct.pack_into('<Q',actual,offset+0x100,(ptr-n.manager-0x608)//64+1)
        wanted=bytes.fromhex(c['after']);diff=[(hex(i),x,y)for i,(x,y)in enumerate(zip(actual,wanted))if x!=y];assert not diff,(index,c['resourceIndex'],c['id'],c['opcode'],diff);digest.update(actual)
    report=dict(scope=__doc__,cases=len(data['cases']),resources=len(data['refs']),stateSha256=digest.hexdigest(),sourceSha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in ['shared/th06nc/anm-rebind.mjs','shared/th06nc/ecl-command.mjs','shared/th06nc/anm-vm.mjs']},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-ecl-anm-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
