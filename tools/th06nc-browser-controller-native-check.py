"""Actual XInput raw packet extractionadc0c..add6a versus browser adapter.
Complete26-byte packet and normalized18-byte button view. XInput state data
supplied; browser axes use explicit sign-normalized int16 fixture values.
No browser driver/OS/device enumeration or physical hardware equivalence claim.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *
def main():
 source='shared/th06nc/browser-controller.mjs';h=hashlib.sha256((ROOT/source).read_bytes()).hexdigest();script="""
import{readBrowserController}from'./shared/th06nc/browser-controller.mjs';const cases=[],digital=[0,1,2,3,4,5,8,9,10,11,12,13,14,15],xinputBits=[12,13,14,15,8,9,5,4,6,7,0,1,2,3],hex=b=>Buffer.from(b).toString('hex');
function test(mask,triggers=[0,0],axes=[0,0,0,0]){const buttons=Array.from({length:17},()=>({pressed:false,value:0}));let bits=0;digital.forEach((index,i)=>{if(mask&(1<<i)){buttons[index]={pressed:true,value:1};bits|=1<<xinputBits[i];}});triggers.forEach((value,i)=>buttons[6+i]={pressed:value>=128,value:value/255});const normalized=axes.map((value,i)=>value/(value<0?32768:32767)*(i%2?-1:1)),result=readBrowserController({connected:true,mapping:'standard',buttons,axes:normalized});cases.push({bits,triggers,axes,packet:hex(result.packet),buttons:hex(result.buttons)});}
for(let mask=0;mask<16384;mask++)test(mask);
for(const left of[0,1,29,30,31,128,255])for(const right of[0,1,29,30,31,128,255])for(const x of[-32768,-10000,-1,0,1,10000,32767])test(0x1555,[left,right],[x,-x===32768?32767:-x,x,x]);
console.log(JSON.stringify(cases));
""";cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256()
 for index,c in enumerate(cases):
  bp=n.stack+0x8100;m.mem_write(n.owner+0xbc,bytes(26));m.mem_write(bp-0x29,struct.pack('<IHBB4h',123,c['bits'],*c['triggers'],*c['axes']));m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.reg_write(UC_X86_REG_RBP,bp);m.reg_write(UC_X86_REG_RBX,n.owner);m.emu_start(0x1400adc0c,0x1400add6a,count=1000);actual=bytes(m.mem_read(n.owner+0xbc,26));assert actual.hex()==c['packet'],(index,'packet',actual.hex(),c);buttons=actual[:16]+bytes([actual[16]>=30,actual[17]>=30]);assert buttons.hex()==c['buttons'],(index,'buttons');digest.update(actual)
 assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==h;report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256={source:h},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-browser-controller-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['passed','cases','stateSha256']}))
if __name__=='__main__':main()
