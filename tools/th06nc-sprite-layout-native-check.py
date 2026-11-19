"""Logical sprite dimensions from the original ANM loader on all ANM resources.

Includes explicit dimensions and zero-extra fallback. No GPU/rendering claim.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT

def main():
    script="""
import{readFileSync}from'node:fs';import{readAnm}from'./shared/th06nc/anm.mjs';import{spriteLogicalSize}from'./shared/th06nc/sprite-layout.mjs';const refs=JSON.parse(readFileSync('artifacts/th06nc/scripts.json')).filter(f=>f.name.endsWith('.anm')).map(f=>({...f,file:f.name,archive:f.path.replaceAll('\\\\','/').split('/').at(-2),slot:8,base:0}));console.log(JSON.stringify(refs.map(r=>({ref:r,sprites:readAnm(readFileSync(r.path)).sprites.map(s=>({id:s.id,size:spriteLogicalSize(s),fallback:s.extra.some(v=>v===0)}))}))));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();digest=hashlib.sha256();count=0;fallback=0
    for c in cases:
        n.load_title([c['ref']])
        for sprite in c['sprites']:
            actual=bytes(n.m.mem_read(n.manager+0x608+sprite['id']*64+0x1c,8));assert actual==struct.pack('<2f',*sprite['size']),(c['ref']['file'],sprite['id'],struct.unpack('<2f',actual),sprite['size']);count+=1;fallback+=sprite['fallback'];digest.update(actual)
    report=dict(scope=__doc__,resources=len(cases),sprites=count,spritesWithFallback=fallback,stateSha256=digest.hexdigest(),sourceSha256=hashlib.sha256((ROOT/'shared/th06nc/sprite-layout.mjs').read_bytes()).hexdigest(),executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-sprite-layout-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
