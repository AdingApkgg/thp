"""Player position integration and combat query bounds, 69384..694f6.

Uses supplied movement velocities/bounds; input selection is checked separately.
Full state bytes compared. Animation, shooting and lifecycle excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *

def main():
    source='shared/th06nc/player-motion.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
    script="""
import{createHash}from'node:crypto';import{playerInputVelocity}from'./shared/th06nc/player-input.mjs';import{integratePlayerMovement}from'./shared/th06nc/player-motion.mjs';const cases=[];for(let input=0;input<256;input++)for(const position of [[192,384,0.2],[-10,-20,0.2],[0,0,0.2],[384,448,0.2],[400,480,0.2]])for(const bounds of [[0,0,384,448],[8,16,368,416]]){
 const state=new Uint8Array(0xa300),v=new DataView(state.buffer),r=playerInputVelocity(input,{speed:4,focusSpeed:2,diagonalSpeed:Math.fround(4/Math.SQRT2),diagonalFocusSpeed:Math.fround(2/Math.SQRT2)});v.setFloat32(0x7710,0.5,true);v.setFloat32(0x7714,1.25,true);position.forEach((x,k)=>v.setFloat32(0x7730+k*4,x,true));[2,3,0].forEach((x,k)=>v.setFloat32(0x9f28+k*4,x,true));const b=Buffer.alloc(8);b.writeFloatLE(r.x);b.writeFloatLE(r.y,4);integratePlayerMovement(state,{velocity:[r.x,r.y],bounds});cases.push({position,bounds,velocity:b.toString('hex'),sha256:createHash('sha256').update(state).digest('hex')});
}console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256()
    for index,c in enumerate(cases):
        initial=bytearray(0xa300);struct.pack_into('<2f',initial,0x7710,0.5,1.25);struct.pack_into('<3f',initial,0x7730,*c['position']);struct.pack_into('<3f',initial,0x9f28,2,3,0);m.mem_write(n.owner,bytes(initial));m.mem_write(0x1404ff0e0,struct.pack('<4f',*c['bounds']));velocity=bytes.fromhex(c['velocity']);m.reg_write(UC_X86_REG_RDI,n.owner);m.reg_write(UC_X86_REG_RBX,n.owner+0x789c);m.reg_write(UC_X86_REG_XMM6,int.from_bytes(velocity[:4],'little'));m.reg_write(UC_X86_REG_XMM7,int.from_bytes(velocity[4:],'little'));m.emu_start(0x140069384,0x1400694f6,count=10000);actual=bytes(m.mem_read(n.owner,0xa300));assert hashlib.sha256(actual).hexdigest()==c['sha256'],(index,c);digest.update(actual)
    assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha
    report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-player-motion-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
