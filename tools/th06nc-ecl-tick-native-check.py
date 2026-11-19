"""Coupled ECL update: script, polar motion, frame tail and clock commit.

Runs the original ECL update to its epilogue. Synthetic programs exercise
supported commands with supplied trig. World manager and gameplay excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    script="""
import{readEcl}from'./shared/th06nc/ecl.mjs';import{EclOperands}from'./shared/th06nc/ecl-operands.mjs';import{NativeRng}from'./shared/th06nc/rng.mjs';import{EclDispatch}from'./shared/th06nc/ecl-dispatch.mjs';import{tickEclEnemy}from'./shared/th06nc/ecl-tick.mjs';
const bits=x=>{const b=Buffer.alloc(4);b.writeFloatLE(x);return b.readUInt32LE();},cases=[];
const variants=[...([0,1,3,5].flatMap(loops=>[0,1,2,3,4].map(difficulty=>({loops,difficulty})))),...([29,30,31,32,33,34].flatMap(jumpOpcode=>[-1,0,1].map(cmpValue=>({loops:3,difficulty:0,jumpOpcode,cmpValue})))),...([37,38,39,40,41,42].flatMap(callOpcode=>[5,9,13].map(callValue=>({loops:1,difficulty:0,callOpcode,callValue})))),{loops:1,difficulty:0,pending:true},{loops:3,difficulty:2,pending:true}];
for(const {loops,difficulty,jumpOpcode=31,cmpValue=0,callOpcode=37,callValue=5,pending=false}of variants){
 const sub=[[
 [0,4,[-10001,loops]],[0,35,[1,callValue,bits(1.5)],255,'call'],[0,3,[0,0,-10001]],
 [0,27,[-10001,cmpValue]],[0,jumpOpcode,[0,0]],[0,113,[999]],[0,114,[44],5,'equal'],[1,116,[77]],[2,1,[]]
 ],[[0,13,[-10001,-10001,1]],[0,5,[-10005,bits(1.5)]],[0,callOpcode,[2,7,bits(2.5),-10001,10]],[0,36,[]]],[[0,45,[bits(0.25),bits(2.5),0]],[0,36,[]]]];
 let offset=28;const offsets=[],records=[];for(const rows of sub){offsets.push(offset);for(const r of rows){r.push(offset);offset+=12+r[2].length*4;records.push(r);}offset+=12;}
 // The final element stores the absolute offset independent of optional labels.
 const pos=r=>r.at(-1);sub[0][2][2][1]=pos(sub[0][1])-pos(sub[0][2]);sub[0][4][2][1]=pos(sub[0][6])-pos(sub[0][4]);
 const bytes=Buffer.alloc(offset);bytes.writeUInt16LE(3);offsets.forEach((p,i)=>bytes.writeUInt32LE(p,16+i*4));
 for(const rows of sub){for(const r of rows){const p=pos(r);bytes.writeInt32LE(r[0],p);bytes.writeInt16LE(r[1],p+4);bytes.writeUInt16LE(12+r[2].length*4,p+6);bytes[p+9]=r.length>=5&&typeof r[3]==='number'?r[3]:255;r[2].forEach((x,i)=>bytes.writeUInt32LE(x>>>0,p+12+i*4));}const p=pos(rows.at(-1))+12+rows.at(-1)[2].length*4;bytes.writeInt32LE(-1,p);bytes.writeInt16LE(-1,p+4);bytes.writeUInt16LE(12,p+6);}
 const enemy=new Uint8Array(0x1100),operands=new EclOperands(enemy,{difficulty,rng:new NativeRng(0xbeef,99),atan2:()=>0.875}),services={operands,sin:()=>0.25,cos:()=>0.75,atan2:()=>0.875,soundSlots:[-1,-1,-1]},vm=new EclDispatch(readEcl(bytes),enemy,services);vm.start();vm.v.setInt16(0xf6c,-1,true);vm.v.setInt32(0x234,500,true);if(pending){vm.v.setInt32(0xf70,0,true);vm.v.setInt32(8,2,true);}
 for(let frame=0;frame<4;frame++){
 const before=Buffer.from(enemy).toString('hex'),result=tickEclEnemy(vm),after=Buffer.from(enemy).toString('hex');cases.push({program:bytes.toString('hex'),difficulty,frame,before,result,after});if(result.deleted)break;
 }
}
console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256();executed=0
    def hook(m,a,size,u):
        nonlocal executed
        if a==0x1400221b1:executed+=1
        if a==0x140028838:m.emu_stop()
        elif a in [0x1402be065,0x1402be071,0x1402be07d]:
            value={0x1402be065:0.875,0x1402be071:0.75,0x1402be07d:0.25}[a];m.reg_write(UC_X86_REG_XMM0,int.from_bytes(struct.pack('<f',value),'little'));sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    m.hook_add(UC_HOOK_CODE,hook)
    for index,c in enumerate(cases):
        program=bytes.fromhex(c['program']);m.mem_write(n.assets,program);count=struct.unpack_from('<H',program)[0]
        for i in range(count):m.mem_write(n.manager+i*8,struct.pack('<Q',n.assets+struct.unpack_from('<I',program,16+i*4)[0]))
        m.mem_write(0x140a6eb80,struct.pack('<Q',n.manager));m.mem_write(0x1404f27c0,struct.pack('<i',c['difficulty']))
        state=bytearray.fromhex(c['before'])
        for p in [0x88,*[0xcb0+i*96 for i in range(8)]]:
            ptr=struct.unpack_from('<Q',state,p)[0]
            if ptr:struct.pack_into('<Q',state,p,n.assets+ptr)
        m.mem_write(n.owner,bytes(state));sp=n.stack+0x8000
        for reg,value in [(UC_X86_REG_RSP,sp),(UC_X86_REG_RBP,n.stack+0x9000),(UC_X86_REG_RDI,n.owner),(UC_X86_REG_R13,n.owner+0x40),(UC_X86_REG_R10,0x140000000),(UC_X86_REG_R12,0),(UC_X86_REG_XMM8,0),*[(r,int.from_bytes(struct.pack('<f',x),'little'))for r,x in [(UC_X86_REG_XMM9,3.1415927410125732),(UC_X86_REG_XMM10,6.2831854820251465),(UC_X86_REG_XMM11,-3.1415927410125732),(UC_X86_REG_XMM12,-6.2831854820251465)]],(UC_X86_REG_R15,1),(UC_X86_REG_RBX,0x9630),(UC_X86_REG_R11,0x6553),(UC_X86_REG_R9,0xffffffffffffffff)]:m.reg_write(reg,value)
        executed=0;m.emu_start(0x140022170,0x140028d13,count=1000000)
        assert executed==c['result']['executed'],(index,executed,c['result']);assert m.reg_read(UC_X86_REG_RIP) in [0x140028d13,0x140028838],hex(m.reg_read(UC_X86_REG_RIP))
        assert (m.reg_read(UC_X86_REG_RIP)==0x140028838)==c['result']['deleted'],index
        assert m.reg_read(UC_X86_REG_R14)-n.assets==c['result']['nextOffset'],(index,hex(m.reg_read(UC_X86_REG_R14)),c['result'])
        actual=bytearray(m.mem_read(n.owner,0x1100))
        for p in [0x88,*[0xcb0+i*96 for i in range(8)]]:
            ptr=struct.unpack_from('<Q',actual,p)[0]
            if ptr:struct.pack_into('<Q',actual,p,ptr-n.assets)
        wanted=bytes.fromhex(c['after']);diff=[(hex(i),x,y)for i,(x,y)in enumerate(zip(actual,wanted))if x!=y];assert not diff,(index,c['frame'],diff);digest.update(actual)
    report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in ['shared/th06nc/ecl-dispatch.mjs','shared/th06nc/ecl-command.mjs','shared/th06nc/ecl-operands.mjs','shared/th06nc/ecl-tick.mjs','shared/th06nc/ecl-motion.mjs','shared/th06nc/ecl-enemy-tail.mjs']},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-ecl-tick-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
