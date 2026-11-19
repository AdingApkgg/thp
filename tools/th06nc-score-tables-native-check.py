"""Native default ranks, unsigned insertion/ties and initial 8-byte name.

Default 7408a prototype records, actual 6cbc0 linked list and 73ff3 name
initialization. Allocation/memset are host services; default list insertion
and final UI/save serialization are outside the default-record subcheck.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/'+s+'.mjs'for s in ['score-file','score-tables']];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources};script="""
import{createDefaultScoreTables,createHighScoreRecord,insertHighScore,sanitizeScoreName}from'./shared/th06nc/score-tables.mjs';const hex=b=>Buffer.from(b).toString('hex'),defaults=[...createDefaultScoreTables().values()].flat().map(hex),cases=[];let random=0x1234abcd;const next=()=>{random^=random<<13;random^=random>>>17;random^=random<<5;return random>>>0;};
for(let scene=0;scene<64;scene++){const table=[],steps=[];for(let i=0;i<24;i++){const score=[0n,1n,100000n,1000000n,9999999990n,0x7fffffffffffffffn,0x8000000000000000n,0xffffffffffffffffn,BigInt(next())][(scene+i)%9],record=createHighScoreRecord({score,name:'N'+String(scene).padStart(2,'0')+String(i).padStart(2,'0'),character:scene%4,difficulty:scene%5,mode:scene%3,stage:i+1}),rank=insertHighScore(table,record);steps.push({record:hex(record),rank,table:table.map(hex)});}cases.push(steps);}
const inputs=[[],[0],[32],[126],[31,127,128,255,65,0,66],[65,66,67,68,69,70,71,72,73],[65,0,66],Array.from(new TextEncoder().encode('东方姓名')),Array.from(new TextEncoder().encode('Nanashi '))],names=inputs.map(input=>({input,result:hex(sanitizeScoreName(Uint8Array.from(input)))}));console.log(JSON.stringify({defaults,cases,names}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;mode='defaults';cursor=n.vm+0x4000;digest=hashlib.sha256()
    m.mem_write(0x1402c0370,struct.pack('<Q',n.vm+0x9000))
    def hook(m,a,size,u):
        nonlocal cursor
        if a==0x14006cbc0 and mode!='defaults':return
        if a==0x14006d1e0:m.emu_stop();return
        sp=m.reg_read(UC_X86_REG_RSP)
        if a==n.vm+0x9000:
            amount=m.reg_read(UC_X86_REG_RCX);out=cursor;cursor+=(amount+15)&~15;assert cursor<n.vm+0x9000;m.mem_write(out,bytes(amount));m.reg_write(UC_X86_REG_RAX,out)
        elif a==0x1402bdee2:
            m.mem_write(m.reg_read(UC_X86_REG_RCX),bytes([m.reg_read(UC_X86_REG_RDX)&255])*m.reg_read(UC_X86_REG_R8));m.reg_write(UC_X86_REG_RAX,m.reg_read(UC_X86_REG_RCX))
        m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [n.vm+0x9000,0x14006cbc0,0x14006d1e0,0x1402bdee2]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    m.mem_write(n.owner,bytes(0x10000));m.reg_write(UC_X86_REG_R15,n.owner);m.reg_write(UC_X86_REG_R13,0);m.reg_write(UC_X86_REG_R8D,10);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x14007408a,0x140074156,count=1000000);actual=bytes(m.mem_read(n.owner+0x49f8,600*36));expected=b''.join(bytes.fromhex(r)for r in data['defaults']);assert actual==expected,'default records';digest.update(actual);mode='insert';head=n.vm+0x1000
    for scene,steps in enumerate(data['cases']):
        cursor=n.vm+0x4000;m.mem_write(head,bytes(24))
        for index,s in enumerate(steps):
            record=bytes.fromhex(s['record']);ptr=n.owner+index*64;m.mem_write(ptr,record);sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,head);m.reg_write(UC_X86_REG_RDX,ptr);m.emu_start(0x14006cbc0,n.stack+0xf000,count=100000);assert m.reg_read(UC_X86_REG_EAX)==s['rank'],(scene,index,'rank');node=struct.unpack('<Q',m.mem_read(head+16,8))[0];rows=[];previous=head
            while node:
                recordPtr,back,nodeNext=struct.unpack('<3Q',m.mem_read(node,24));rows.append(bytes(m.mem_read(recordPtr,36)).hex());previous=node;node=nodeNext
            assert rows==s['table'],(scene,index,'linked list');digest.update(bytes.fromhex(''.join(rows)))
    mode='name'
    for index,s in enumerate(data['names']):
        m.mem_write(n.owner,bytes(0x10000));m.mem_write(n.owner+0x9e9a,b'\1');m.mem_write(0x140c21dc4,bytes(128));m.mem_write(0x140c21dc4,bytes(s['input']));m.reg_write(UC_X86_REG_R15,n.owner);m.reg_write(UC_X86_REG_R13,0);m.reg_write(UC_X86_REG_R8D,10);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x140073ff3,0x140074085,count=100000);actual=bytes(m.mem_read(n.owner+0x9e88,9));assert actual.hex()==s['result'],(index,'name');digest.update(actual)
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items());report=dict(scope=__doc__,defaultRecords=len(data['defaults']),insertionScenes=len(data['cases']),insertions=sum(len(s)for s in data['cases']),nameCases=len(data['names']),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-score-tables-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
