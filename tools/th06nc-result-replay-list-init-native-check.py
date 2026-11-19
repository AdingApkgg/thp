"""Replay-list entry 6d310, state reset and sixty header reads.

Real result/result00..03/difficulty/text ANMs; complete bb48-byte owner
with script/resource/sprite pointer normalization.
Original 7583c, 73e93, 6d310/6d1e0 execute. Controlled headers/services;
Directory, filename formatting, validated/decrypted file headers and free are services. File decode, navigation, drawing and saving excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *
from unicorn import UC_HOOK_CODE

def main():
    sources=['shared/th06nc/'+s+'.mjs'for s in ['result-replay-list-init','sound-queue','result-state','anm-bank','anm-rebind','anm-vm']];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources};script="""
import{initializeResultReplayList}from'./shared/th06nc/result-replay-list-init.mjs';import{readFileSync}from'node:fs';import{createHash}from'node:crypto';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{ResultState,resultAssets,resultTextAsset,advanceResultCommon}from'./shared/th06nc/result-state.mjs';const refs=[...resultAssets,resultTextAsset],sha=b=>createHash('sha256').update(b).digest('hex'),scenes=[];
for(const selection of [0,14,15,59])for(const pattern of [0,1,2])for(const filled of [false,true]){const bank=new AnmBank();for(const r of refs)bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+r.archive+'/'+r.file)),r.base,{slot:r.slot});const state=new ResultState(bank),initialized=sha(state.bytes),initialBytes=scenes.length===0?Buffer.from(state.bytes).toString('hex'):null;state.v.setInt32(0x4438,selection,true);state.v.setInt32(0x4450,80,true);if(filled)state.bytes.fill(0xa5,0x9eb0,0xbad0);const sounds=[-1,-1,-1],events=[];initializeResultReplayList(state,{soundSlots:sounds,ensureDirectory:path=>events.push({kind:'directory',path}),readHeader:(path,slot)=>{events.push({kind:'readHeader',path,slot});if(pattern===0||(pattern===1&&slot%2))return null;return Uint8Array.from({length:120},(_,i)=>(slot*3+i)&255);}});scenes.push({selection,pattern,filled,initialized,initialBytes,sounds,events,expected:sha(state.bytes)});}console.log(JSON.stringify({refs,scenes}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;n.load_title(data['refs']);offsets=[0xb0+i*288 for i in range(38)]+[0x2b70+i*288 for i in range(16)]+[0x3d70+i*288 for i in range(5)]+[0x4310];digest=hashlib.sha256();checked=0
    def normalized():
        raw=bytearray(m.mem_read(n.owner,0xbb48))
        for offset in offsets:
            for field in [0xf0,0xf8]:
                p=offset+field;ptr=struct.unpack_from('<Q',raw,p)[0]
                if ptr:struct.pack_into('<Q',raw,p,ptr-next(lo for lo,hi in n.ranges if lo<=ptr<hi))
            p=offset+0x100;ptr=struct.unpack_from('<Q',raw,p)[0]
            if ptr:struct.pack_into('<Q',raw,p,(ptr-n.manager-0x608)//64+1)
        return bytes(raw)
    events=[];pattern=0
    for ptr,shim in [(0x1402c0350,n.vm+0x9000),(0x1402c0378,n.vm+0x9010)]:m.mem_write(ptr,struct.pack('<Q',shim))
    def cstring(p):return bytes(m.mem_read(p,100)).split(b'\0')[0].decode()
    def hook(m,a,size,u):
        sp=m.reg_read(UC_X86_REG_RSP)
        if a==n.vm+0x9000:events.append(dict(kind='directory',path=cstring(m.reg_read(UC_X86_REG_RCX))))
        elif a==0x140038740:
            slot=m.reg_read(UC_X86_REG_R8D);assert cstring(m.reg_read(UC_X86_REG_RDX))=='replay/th6_%.2d.rpy';m.mem_write(m.reg_read(UC_X86_REG_RCX),f'replay/th6_{slot:02d}.rpy'.encode()+b'\0')
        elif a==0x14006af60:
            path=cstring(m.reg_read(UC_X86_REG_RCX));slot=int(path[-6:-4]);events.append(dict(kind='readHeader',path=path,slot=slot));ptr=n.vm+0x2000+slot*128
            if pattern==0 or(pattern==1 and slot%2):ptr=0
            else:m.mem_write(ptr,bytes((slot*3+i)&255 for i in range(120)))
            m.reg_write(UC_X86_REG_RAX,ptr)
        m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [n.vm+0x9000,n.vm+0x9010,0x140038740,0x14006af60,0x1402bcf20]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    for index,s in enumerate(data['scenes']):
        m.mem_write(n.owner,bytes(0xbb48));m.mem_write(n.owner+0x9e7c,struct.pack('<i',1));m.reg_write(UC_X86_REG_RDI,0x7d0);m.reg_write(UC_X86_REG_RBX,n.owner+0x3d70);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x14007583c,0x140075a34,count=1000000);m.reg_write(UC_X86_REG_R15,n.owner);m.reg_write(UC_X86_REG_R13,0);m.reg_write(UC_X86_REG_R12D,0x798);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x140073e93,0x140073ff3,count=1000000);actual=normalized();assert hashlib.sha256(actual).hexdigest()==s['initialized'],(index,'init',[(hex(i),a,b)for i,(a,b)in enumerate(zip(actual,bytes.fromhex(data['scenes'][0]['initialBytes'])))if a!=b][:25]);digest.update(actual);m.mem_write(n.owner+0x4438,struct.pack('<i',s['selection']));m.mem_write(n.owner+0x4450,struct.pack('<i',80));pattern=s['pattern'];events.clear();m.mem_write(0x140509670,struct.pack('<3i',-1,-1,-1));m.mem_write(0x140509694,b'\0')
        if s['filled']:m.mem_write(n.owner+0x9eb0,bytes([0xa5])*(0xbad0-0x9eb0))
        sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.emu_start(0x14006d310,n.stack+0xf000,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000;actual=normalized();assert hashlib.sha256(actual).hexdigest()==s['expected'],(index,'owner');assert events==s['events'],(index,'services',events[:3],s['events'][:3]);assert list(struct.unpack('<3i',m.mem_read(0x140509670,12)))==s['sounds'],(index,'sounds');digest.update(actual);checked+=1
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items());report=dict(scope=__doc__,scenes=len(data['scenes']),frames=checked,animationVms=60,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-result-replay-list-init-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
