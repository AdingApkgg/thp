"""Native 319d..31e7 top/bottom vertex alpha byte rounding, all byte pairs.

Reads all four generated alpha bytes; additionally executes actual cropped and
uncropped 2a80 through 3385 to verify top/bottom vertex orientation and RGB.
Pixel snapping is disabled for those orientation scenes; GPU is excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *

def main():
 source='shared/th06nc/anm-vertex-alpha.mjs';before=hashlib.sha256((ROOT/source).read_bytes()).hexdigest();expected=bytes.fromhex(subprocess.check_output(['node','--input-type=module','-e',"import{anmVertexAlphas}from'./shared/th06nc/anm-vertex-alpha.mjs';const bytes=[];for(let alpha=0;alpha<256;alpha++)for(let top=0;top<256;top++)bytes.push(...anmVertexAlphas(((alpha<<24)|0x224466)>>>0,top,255-top));console.log(Buffer.from(bytes).toString('hex'));"],cwd=ROOT,text=True).strip());n=Native();m=n.m;output=bytearray()
 for alpha in range(256):
  m.mem_write(n.owner+0xef,bytes([alpha]))
  for top in range(256):
   for reg,value in [(UC_X86_REG_RBX,n.owner),(UC_X86_REG_R14,top),(UC_X86_REG_RSI,255-top)]:m.reg_write(reg,value)
   m.emu_start(0x14000319d,0x1400031e7,count=1000);values=[m.mem_read(p,1)[0]for p in [0x140a6eaf3,0x140a6eb0f,0x140a6eb2b,0x140a6eb47]];assert values[0]==values[1]and values[2]==values[3];output.extend([values[0],values[2]])
 assert bytes(output)==expected
 n.load_title([dict(archive='th06IN.dat',file='text.anm',slot=0,base=0x72f)]);orientation=[]
 for alpha in [127,255]:
  for top,bottom in [(30,220),(255,0)]:
   for cropped in [False,True]:
    b=bytearray(288)
    for p,value in [(0xc4,0x403),(0xec,(alpha<<24)|0x224466),(0x114,100 if cropped else 0),(0x118,15 if cropped else 0)]:struct.pack_into('<I',b,p,value)
    for p,value in [(0xe4,1),(0xe8,1),(0xc8,10),(0xcc,20)]:struct.pack_into('<f',b,p,value)
    struct.pack_into('<Q',b,0x100,n.manager+0x608+0x737*64);m.mem_write(n.owner,bytes(b));m.mem_write(0x140c21e48,struct.pack('<I',1080));m.mem_write(0x140c21e44,struct.pack('<I',1920));sp=n.stack+0x8000;m.mem_write(sp+0x28,b'\0')
    for reg,value in [(UC_X86_REG_RCX,n.manager),(UC_X86_REG_RDX,n.owner),(UC_X86_REG_R8,top),(UC_X86_REG_R9,bottom),(UC_X86_REG_RSP,sp)]:m.reg_write(reg,value)
    m.emu_start(0x140002a80,0x140003385,count=100000);vertices=[struct.unpack('<4fI2f',m.mem_read(0x140a6eae0+i*28,28))for i in range(4)];assert vertices[0][1]==vertices[1][1]and vertices[2][1]==vertices[3][1]and vertices[0][1]<vertices[2][1]
    expected_alpha=[(alpha*top+127)//255]*2+[(alpha*bottom+127)//255]*2;assert [v[4]>>24 for v in vertices]==expected_alpha;assert all(v[4]&0xffffff==0x224466 for v in vertices);orientation.append(dict(alpha=alpha,top=top,bottom=bottom,cropped=cropped,vertices=vertices))
 assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==before
 report=dict(scope=__doc__,cases=65536,orientationCases=orientation,stateSha256=hashlib.sha256(output).hexdigest(),sourceSha256={source:before},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-anm-vertex-alpha-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'cases':65536,'stateSha256':report['stateSha256']}))

if __name__=='__main__':main()
