"""Native 2af1..2e05 cropped XY/UV geometry for real text ANM.

All seven anchor values, signed scale, target sizes and crop rectangles compare
float32 vertex bytes. Snap, rotation, sampling/blend and GPU pixels excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *

def main():
    source='shared/th06nc/anm-quad.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest();script="""
import{readFileSync}from'node:fs';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{rebindAnm}from'./shared/th06nc/anm-rebind.mjs';import{anmQuad}from'./shared/th06nc/anm-quad.mjs';const ref={archive:'th06IN.dat',file:'text.anm',slot:0,base:0x72f},bank=new AnmBank(),cases=[];bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+ref.archive+'/'+ref.file)),ref.base,{slot:ref.slot});for(const id of [0x730,0x731,0x732,0x733])for(const anchor of [0,0x100,0x200,0x300,0x400,0x500,0x600])for(const height of [480,720,1080])for(const crop of [[0,72,1,36],[17,108,99,36],[0,36,700,0],[-5,-7,2048,48]])for(const scale of [[1,1],[.5,2],[-1,1]]){const vm=rebindAnm(bank,id,new Uint8Array(288)),v=vm.v;v.setUint32(0xc4,(v.getUint32(0xc4,true)&~0x700)|anchor|3,true);v.setUint32(0xec,0xffffffff,true);crop.forEach((x,i)=>v.setInt32(0x10c+i*4,x,true));v.setFloat32(0xe8,scale[0],true);v.setFloat32(0xe4,scale[1],true);v.setFloat32(0xc8,100.25,true);v.setFloat32(0xcc,200.5,true);v.setFloat32(0x2c,.125,true);v.setFloat32(0x30,-.0625,true);v.setFloat32(0xa4,0,true);cases.push({height,state:Buffer.from(vm.state).toString('hex'),quad:Buffer.from(anmQuad(vm,height).buffer).toString('hex')});}console.log(JSON.stringify({ref,cases}));
""";data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();n.load_title([data['ref']]);m=n.m;digest=hashlib.sha256()
    for index,c in enumerate(data['cases']):
        state=bytearray.fromhex(c['state']);sprite=struct.unpack_from('<Q',state,0x100)[0];struct.pack_into('<Q',state,0x100,n.manager+0x608+(sprite-1)*64);m.mem_write(n.vm,bytes(state));m.mem_write(0x140c21e48,struct.pack('<I',c['height']));m.reg_write(UC_X86_REG_RDX,n.vm);m.reg_write(UC_X86_REG_EAX,struct.unpack_from('<I',state,0x114)[0]);m.emu_start(0x140002af1,0x140002e05,count=100000);actual=b''.join(bytes(m.mem_read(0x140a6ec70+j*24,8))+bytes(m.mem_read(0x140a6ec80+j*24,8))for j in range(4));assert actual.hex()==c['quad'],(index,struct.unpack('<16f',actual),struct.unpack('<16f',bytes.fromhex(c['quad'])));digest.update(actual)
    assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha;report=dict(scope=__doc__,cases=len(data['cases']),stateSha256=digest.hexdigest(),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-anm-crop-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
