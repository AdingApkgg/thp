"""Normal and score-item popup rings: original 9bd0 and inline 436a7 block.

Complete 515-slot storage, ring wrap, signed values and untouched old digit
bytes compared. Popup animation, font sprites and draw excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *

def main():
    source='shared/th06nc/score-popup-pool.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
    script="""
import{createHash}from'node:crypto';import{ScorePopupPool}from'./shared/th06nc/score-popup-pool.mjs';const cases=[];for(const small of [false,true])for(const cursor of [0,2,3,511,512,513])for(const value of [-99,-1,0,1,9,10,12800,2147483647])for(const fill of [0,85])for(const color of [0xffffffff,0xff80c0ff]){const pool=new ScorePopupPool();pool.storage.fill(fill);pool.cursor=cursor;pool.smallCursor=cursor;const slot=(small?pool.publishSmall({position:[100.5,200.25,0.49],value}):pool.publish({position:[100.5,200.25,0.49],value,color}));cases.push({small,cursor,value,fill,color,slot,next:pool.cursor,smallNext:pool.smallCursor,sha256:createHash('sha256').update(pool.storage).digest('hex')});}console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;base=0x1403de870;digest=hashlib.sha256()
    for index,c in enumerate(cases):
        m.mem_write(base,bytes([c['fill']])*(515*40));m.mem_write(0x1403de628,struct.pack('<2i',c['cursor'],c['cursor']));m.mem_write(n.vm,struct.pack('<3f',100.5,200.25,0.49));m.mem_write(n.vm+0x10,struct.pack('<3f',100.5,200.25,0.49));m.reg_write(UC_X86_REG_R8D,c['value']&0xffffffff);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000)
        if c['small']:m.reg_write(UC_X86_REG_RSI,0x140000000);m.reg_write(UC_X86_REG_R14,n.vm);m.reg_write(UC_X86_REG_RBP,0);m.emu_start(0x1400436a7,0x140043771,count=100000)
        else:
            m.reg_write(UC_X86_REG_RDX,n.vm);m.reg_write(UC_X86_REG_R9D,c['color']);m.mem_write(n.stack+0x8000,struct.pack('<Q',n.stack+0xf000));m.emu_start(0x140009bd0,n.stack+0xf000,count=100000)
        actual=bytes(m.mem_read(base,515*40));assert hashlib.sha256(actual).hexdigest()==c['sha256'],(index,c);assert struct.unpack('<2i',m.mem_read(0x1403de628,8))==(c['next'],c['smallNext']);digest.update(actual)
    assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha
    report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-score-popup-pool-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
