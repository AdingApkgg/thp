"""Full ordinary bullet manager loop, real ANM and lifecycle across 120 frames.

Point-item update and bomb rectangle results are controlled services; exact
rectangle query inputs are compared with the native consumer boundary; a static
invulnerable player disables grazing. Laser manager and full game excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/bullet-pool.mjs','shared/th06nc/bullet-pattern.mjs','shared/th06nc/bullet-motion.mjs','shared/th06nc/bullet-update.mjs'];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
    script="""
import{readFileSync}from'node:fs';import{createHash}from'node:crypto';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{commonProjectileAssetPlan}from'./shared/th06nc/common-layout.mjs';import{BulletPool}from'./shared/th06nc/bullet-pool.mjs';const refs=commonProjectileAssetPlan(),bank=new AnmBank(),hex=b=>Buffer.from(b).toString('hex'),hash=b=>createHash('sha256').update(b).digest('hex');for(const r of refs)bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+r.archive+'/'+r.file)),r.base,{slot:r.slot});const scenes=[];
for(const flags of [0,1,2,4,8,16,32,64,128,256,512,1024,2048,4095])for(const position of [[100,100],[-20,100],[380,440],[100,-20],[192,400]]){
 const pool=new BulletPool({anmBank:bank,environment:{playerPosition:[192,400,0],playerState:2},sin:()=>0.25,cos:()=>0.75,atan2:()=>0.875}),descriptor=new Uint8Array(108),d=new DataView(descriptor.buffer);d.setUint16(0,flags,true);d.setInt16(0x18,1,true);d.setInt16(0x1a,1,true);d.setFloat32(4,3.7,true);d.setFloat32(8,0.4,true);d.setFloat32(0xc,position[0],true);d.setFloat32(0x10,position[1],true);d.setFloat32(0x34,0.5,true);d.setFloat32(0x38,0.6,true);d.setInt32(0x1c,30,true);d.setInt32(0x20,3,true);d.setFloat32(0x40,0.1,true);d.setFloat32(0x44,0.2,true);const entry=pool.spawn(descriptor)[0],initial=hex(entry.bytes),frames=[];
 for(let frame=1;frame<=120;frame++){const queries=[];pool.tick({queryCancel:rect=>{queries.push(rect);return false;}});if([1,2,10,30,60,120].includes(frame))frames.push({frame,queries,state:hex(entry.bytes),sha256:hash(pool.storage),activeCount:pool.activeCount});}scenes.push({flags,position,initial,frames});
}console.log(JSON.stringify({refs,scenes}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();n.load_title(data['refs']);m=n.m;queries=[];base=0x1403ec2a0;size=640*0x620
    def normalize(block,encode=False):
        for j in range(5):
            offset=0x50+j*0x120
            for field in [0xf0,0xf8]:
                p=offset+field;ptr=struct.unpack_from('<Q',block,p)[0]
                if ptr:
                    if encode:asset=n.assetByFile['etama3.anm'];struct.pack_into('<Q',block,p,asset+ptr)
                    else:asset=next(a for a,b in n.ranges if a<=ptr<b);struct.pack_into('<Q',block,p,ptr-asset)
            p=offset+0x100;ptr=struct.unpack_from('<Q',block,p)[0]
            if ptr:struct.pack_into('<Q',block,p,n.manager+0x608+(ptr-1)*64 if encode else(ptr-n.manager-0x608)//64+1)
    def hook(m,a,sz,u):
        if a==0x14006a8c0:
            left=struct.unpack('<f',struct.pack('<I',m.reg_read(UC_X86_REG_XMM1)&0xffffffff))[0];top=struct.unpack('<f',struct.pack('<I',m.reg_read(UC_X86_REG_XMM2)&0xffffffff))[0];right=struct.unpack('<f',struct.pack('<I',m.reg_read(UC_X86_REG_XMM3)&0xffffffff))[0];bottom=struct.unpack('<f',m.mem_read(m.reg_read(UC_X86_REG_RSP)+0x28,4))[0];queries.append(dict(left=left,top=top,right=right,bottom=bottom));m.reg_write(UC_X86_REG_RAX,0)
        elif a==0x1402bdee2:m.mem_write(m.reg_read(UC_X86_REG_RCX),bytes(m.reg_read(UC_X86_REG_R8)));m.reg_write(UC_X86_REG_RAX,m.reg_read(UC_X86_REG_RCX))
        elif a in [0x1402be065,0x1402be071,0x1402be07d]:m.reg_write(UC_X86_REG_XMM0,int.from_bytes(struct.pack('<f',0.875 if a==0x1402be065 else 0.75 if a==0x1402be071 else 0.25),'little'))
        else:m.reg_write(UC_X86_REG_RAX,0)
        sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x140042980,0x14006a8c0,0x14006a980,0x1402bdee2,0x1402be065,0x1402be071,0x1402be07d]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    m.mem_write(0x140506c38,b'\2');m.mem_write(0x140506ad0,struct.pack('<3f',192,400,0));m.mem_write(0x1404f27b9,b'\0');digest=hashlib.sha256();checked=0
    for sceneIndex,scene in enumerate(data['scenes']):
        initial=bytearray.fromhex(scene['initial']);normalize(initial,True);m.mem_write(base+8,bytes(size));m.mem_write(base+8,bytes(initial));last=0
        for expected in scene['frames']:
            for frame in range(last+1,expected['frame']+1):queries.clear();m.reg_write(UC_X86_REG_RCX,base);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x140010870,0x1400115a6,count=1000000)
            last=expected['frame'];assert queries==expected['queries'],(sceneIndex,last,'query inputs',queries,expected['queries']);actual=bytearray(m.mem_read(base+8,size));first=actual[:0x620];normalize(first);actual[:0x620]=first;wanted=bytes.fromhex(expected['state']);assert first==wanted,(sceneIndex,scene['flags'],scene['position'],last,[(hex(p),a,b)for p,(a,b)in enumerate(zip(first,wanted))if a!=b][:20]);assert hashlib.sha256(actual).hexdigest()==expected['sha256'];assert struct.unpack('<i',m.mem_read(base+0xf5008,4))[0]==expected['activeCount'];digest.update(actual);checked+=1
    assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
    report=dict(scope=__doc__,scenes=len(data['scenes']),frames=len(data['scenes'])*120,checkpoints=checked,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-bullet-update-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
