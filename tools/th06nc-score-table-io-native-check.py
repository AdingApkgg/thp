"""All sixty rank tables: actual default/load/filter and HSCR save prefix.

7408a creates defaults; 74219 filters actual record bytes into real 6cbc0
lists; 7458e..747a4 serializes first ten nodes in mode/difficulty/profile order.
Allocator is a host boundary. Other record types, UI and disk writes excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/'+s+'.mjs'for s in ['score-file','score-tables']];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources};script="""
import{createHighScoreRecord,loadHighScoreTables,serializeHighScoreTables}from'./shared/th06nc/score-tables.mjs';const hex=b=>Buffer.from(b).toString('hex'),records=[];for(let mode=0;mode<3;mode++)for(let difficulty=0;difficulty<5;difficulty++)for(let character=0;character<4;character++)for(let rank=0;rank<12;rank++){const score=[0n,1n,99999n,100000n,100001n,999999n,1000000n,1000000n,1000001n,9999999990n,0x8000000000000000n,0xffffffffffffffffn][rank],r=createHighScoreRecord({score,name:'N'+String(rank).padStart(2,'0'),mode,difficulty,character,stage:rank+1});r[9]=77;records.push(r);}for(const field of [8,20,21,22]){const r=createHighScoreRecord({score:9999999999n,name:'INVALID'});r[field]=255;records.push(r);}const unknown=createHighScoreRecord({score:9999999999n});unknown.set([84,69,83,84]);records.push(unknown);const tables=loadHighScoreTables(records);console.log(JSON.stringify({records:records.map(hex),tables:[...tables.values()].map(t=>t.map(hex)),saved:serializeHighScoreTables(tables).map(hex)}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;heap=0x75000000;m.mem_map(heap,0x400000);cursor=heap;digest=hashlib.sha256();m.mem_write(0x1402c0370,struct.pack('<Q',n.vm+0x9000))
    def hook(m,a,size,u):
        nonlocal cursor
        count=m.reg_read(UC_X86_REG_RCX);out=cursor;cursor+=(count+15)&~15;assert cursor<heap+0x400000;m.mem_write(out,bytes(count));m.reg_write(UC_X86_REG_RAX,out);sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    m.hook_add(UC_HOOK_CODE,hook,begin=n.vm+0x9000,end=n.vm+0x9000);m.mem_write(n.owner,bytes(0x10000));m.reg_write(UC_X86_REG_R15,n.owner);m.reg_write(UC_X86_REG_R13,0);m.reg_write(UC_X86_REG_R8D,10);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x14007408a,0x140074156,count=1000000)
    body=b''.join(bytes.fromhex(r)for r in data['records']);m.mem_write(n.assets,struct.pack('<6I',24,0,0,0,len(body)+24,0)+body)
    index=0
    for mode in range(3):
        for difficulty in range(5):
            for character in range(4):
                head=n.owner+0x4458+index*24;m.reg_write(UC_X86_REG_R15,n.assets);m.reg_write(UC_X86_REG_R14,head);m.reg_write(UC_X86_REG_ESI,mode);m.reg_write(UC_X86_REG_R13D,difficulty);m.reg_write(UC_X86_REG_R12D,character);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x140074219,0x1400742d5,count=1000000);node=struct.unpack('<Q',m.mem_read(head+16,8))[0];rows=[]
                while node:
                    ptr=struct.unpack('<Q',m.mem_read(node,8))[0];rows.append(bytes(m.mem_read(ptr,36)).hex());node=struct.unpack('<Q',m.mem_read(node+16,8))[0]
                assert rows==data['tables'][index],(index,'load table');digest.update(bytes.fromhex(''.join(rows)));index+=1
    out=n.assets+0x100000;m.mem_write(out,bytes(0x10000));m.reg_write(UC_X86_REG_R15,n.owner);m.reg_write(UC_X86_REG_R11,n.owner+0x4480);m.reg_write(UC_X86_REG_RBP,out);m.reg_write(UC_X86_REG_EBX,32);m.reg_write(UC_X86_REG_EDI,36);m.reg_write(UC_X86_REG_R12,0);m.reg_write(UC_X86_REG_R14D,3);m.reg_write(UC_X86_REG_R10D,0);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x14007458e,0x1400747a4,count=1000000);actual=bytes(m.mem_read(out+32,m.reg_read(UC_X86_REG_EBX)-32));expected=bytes.fromhex(''.join(data['saved']));assert actual==expected,('save HSCR prefix',len(actual),len(expected));digest.update(actual)
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items());report=dict(scope=__doc__,tables=index,inputRecords=len(data['records']),loadedRecords=sum(len(t)for t in data['tables']),savedRecords=len(data['saved']),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-score-table-io-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
