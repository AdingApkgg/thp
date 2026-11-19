"""Whole ANM text publisher 7530: real destination sprites and font metadata.

Native font/GPU routine is an observed service, computing its already-verified
layout with independent metadata. Full VM bytes, font selection, destination,
missing-cache preservation and crop metrics compared; GPU pixels excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/font-publish.mjs','shared/th06nc/font-atlas.mjs'];hashes={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources};script="""
import{readFileSync}from'node:fs';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{rebindAnm}from'./shared/th06nc/anm-rebind.mjs';import{readFontAtlas}from'./shared/th06nc/font-atlas.mjs';import{publishAnmText}from'./shared/th06nc/font-publish.mjs';const ref={archive:'th06IN.dat',file:'text.anm',slot:0,base:0x72f},bank=new AnmBank(),fonts=new Map(),cases=[],manifest=JSON.parse(readFileSync('artifacts/th06nc/fonts.json'));bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+ref.archive+'/'+ref.file)),ref.base,{slot:ref.slot});for(const f of manifest.fonts.filter(f=>f.bitmapAvailable))fonts.set(f.stem,readFontAtlas(readFileSync('runtimes/th06nc/artifacts/fonts/'+f.stem+'.json','utf8'),readFileSync('runtimes/th06nc/artifacts/fonts/advance_'+f.stem+'.txt','utf8')));
for(const id of [0x730,0x731,0x732,0x733,0x734])for(const size of [0,15,16])for(const colors of [[0xffffff,0,0x10101,0x50505],[0xfff0f0,0,0x10101,0x50505],[0xe0ffff,0,0x10101,0x40202],[0xfffffe,0,0x10101,0x40202]])for(const language of ['zh-CN','en'])for(const text of ['', ' ', 'A12.5 中文か🙂']){
 const vm=rebindAnm(bank,id,new Uint8Array(288)),{v}=vm;v.setUint8(0x108,size);[17,19,23,29].forEach((x,i)=>v.setInt32(0x10c+i*4,x,true));const before=Buffer.from(vm.state).toString('hex'),plans=[];publishAnmText(vm,{text,colors,language,fonts,paint:p=>plans.push({key:p.key,clear:p.clear,glyphs:p.glyphs,metrics:p.metrics})});cases.push({id,size,colors,language,text,before,plans,after:Buffer.from(vm.state).toString('hex')});}console.log(JSON.stringify({ref,cases}));
""";data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();n.load_title([data['ref']]);m=n.m;plans=[];current=None;glyphs={};active=None;digest=hashlib.sha256();manifest=json.loads((ROOT/'artifacts/th06nc/fonts.json').read_bytes());available={f['stem']for f in manifest['fonts']if f['bitmapAvailable']}
    def hook(m,a,size,u):
        nonlocal glyphs,current
        sp=m.reg_read(UC_X86_REG_RSP);size=struct.unpack('<I',m.mem_read(sp+0x28,4))[0];colors=[struct.unpack('<I',m.mem_read(sp+p,4))[0]for p in [0x38,0x40,0x60,0x68]];key=str(size)+'_'+('_'.join(f'0x{x:08X}'for x in colors))+(''if colors[0]==0xfffffe else '_'+active['language'])
        if key in available:
            if current!=key:
                current=key;directory=ROOT/'runtimes/th06nc/artifacts/fonts';glyphs={}
                for line in (directory/f'advance_{key}.txt').read_text().splitlines():
                    if line:cp,advance=line.split('\t');glyphs[int(cp,16)]=dict(advance=float(advance),source=[0,0,0,0])
                for frame in json.loads((directory/f'{key}.json').read_bytes())['frames']:
                    cp=int(frame['filename'],16);r=frame['frame'];glyphs.setdefault(cp,dict(advance=0))['source']=[r['x'],r['y'],r['w'],r['h']]
            x=m.reg_read(UC_X86_REG_ECX);y=m.reg_read(UC_X86_REG_EDX);width=m.reg_read(UC_X86_REG_R8D);pointer=struct.unpack('<Q',m.mem_read(sp+0x48,8))[0];text=bytes(m.mem_read(pointer,256)).split(b'\0')[0].decode();currentX=x;fraction=0;outWidth=0;height=0;blits=[]
            for ch in text:
                cp=ord(ch);g=glyphs.get(cp);advance=18
                if g:
                    blits.append(dict(codePoint=cp,source=g['source'],position=[currentX,y]));outWidth=g['source'][2]-x+currentX;height=max(height,g['source'][3]);integer=int(g['advance']);fraction+=g['advance']-integer;advance=integer
                    if fraction>=1:advance+=1;fraction-=1
                currentX=int(currentX+advance)
            metrics=[x,y,outWidth,height];plans.append(dict(key=key,clear=[0,y,width,36],glyphs=blits,metrics=metrics));dest=struct.unpack('<Q',m.mem_read(sp+0x58,8))[0];m.mem_write(dest,struct.pack('<4i',*metrics))
        m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    m.hook_add(UC_HOOK_CODE,hook,begin=0x14007d2c0,end=0x14007d2c0)
    for index,c in enumerate(data['cases']):
        active=c;state=bytearray.fromhex(c['before'])
        for p in [0xf0,0xf8]:
            ptr=struct.unpack_from('<Q',state,p)[0]
            if ptr:struct.pack_into('<Q',state,p,n.assets+ptr)
        p=0x100;sprite=struct.unpack_from('<Q',state,p)[0];struct.pack_into('<Q',state,p,n.manager+0x608+(sprite-1)*64);m.mem_write(n.vm,bytes(state));m.mem_write(n.owner,c['text'].encode()+b'\0');sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.mem_write(sp+0x28,struct.pack('<I',c['colors'][2]));m.mem_write(sp+0x30,struct.pack('<I',c['colors'][3]));m.mem_write(sp+0x38,struct.pack('<Q',n.owner));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.manager);m.reg_write(UC_X86_REG_RDX,n.vm);m.reg_write(UC_X86_REG_R8D,c['colors'][0]);m.reg_write(UC_X86_REG_R9D,c['colors'][1]);plans.clear();m.emu_start(0x140007530,n.stack+0xf000,count=100000);assert plans==c['plans'],(index,'plans',plans,c['plans']);actual=bytearray(m.mem_read(n.vm,288))
        for p in [0xf0,0xf8]:
            ptr=struct.unpack_from('<Q',actual,p)[0]
            if ptr:struct.pack_into('<Q',actual,p,ptr-n.assets)
        ptr=struct.unpack_from('<Q',actual,0x100)[0];struct.pack_into('<Q',actual,0x100,(ptr-n.manager-0x608)//64+1);assert actual.hex()==c['after'],(index,'VM');digest.update(actual)
    assert hashes=={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources};report=dict(scope=__doc__,cases=len(data['cases']),painted=sum(bool(c['plans'])for c in data['cases']),missingCache=sum(not c['plans']for c in data['cases']),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-font-publish-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
