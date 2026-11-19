"""Native 7d455..7d624 glyph layout on all original font metadata sets.

UTF-8 decoding, cache lookup, graphics calls and modf are supplied services;
actual native integer placement/fraction carry and output bounds are compared.
Missing DDS companions do not prevent metadata/layout checks; GPU excluded.
"""
import hashlib,json,math,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    source='shared/th06nc/font-atlas.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
    script="""
import{readFileSync}from'node:fs';import{readFontAtlas,layoutFontText}from'./shared/th06nc/font-atlas.mjs';const fonts=JSON.parse(readFileSync('artifacts/th06nc/fonts.json')).fonts,cases=[];for(const f of fonts){const stem=f.stem,atlas=readFontAtlas(readFileSync('runtimes/th06nc/artifacts/fonts/'+stem+'.json','utf8'),readFileSync('runtimes/th06nc/artifacts/fonts/advance_'+stem+'.txt','utf8')),all=[...atlas.glyphs.keys()].map(cp=>String.fromCodePoint(cp)).join('');for(const text of ['', ' ', 'A12.5 中文か나🙂', 'A\\0ignored',all])for(const origin of [[0,0],[17,-23]])cases.push({stem,text,origin,...layoutFontText(atlas,text,{x:origin[0],y:origin[1]})});}console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;glyphs={};calls=[];sourceRect=None;digest=hashlib.sha256()
    def signed(x):return x if x<0x80000000 else x-0x100000000
    def char(ptr):return bytes(m.mem_read(ptr,4)).decode('utf-8',errors='ignore')[0]
    def hook(m,a,size,u):
        nonlocal sourceRect
        if a==0x14007d4d0:
            cp=m.reg_read(UC_X86_REG_EAX);g=glyphs.get(cp);ptr=n.vm+0x2000 if g else 0
            if g:m.mem_write(ptr+0x18,struct.pack('<d4i',g['advance'],*g['source']))
            m.reg_write(UC_X86_REG_RDI,ptr);m.reg_write(UC_X86_REG_RCX,n.vm+0xf000);m.reg_write(UC_X86_REG_RIP,0x14007d542);return
        if a==0x14007d5b6:
            value=struct.unpack('<d',m.reg_read(UC_X86_REG_XMM0).to_bytes(16,'little')[:8])[0];fraction,integer=math.modf(value);m.mem_write(m.reg_read(UC_X86_REG_RDX),struct.pack('<d',integer));m.reg_write(UC_X86_REG_XMM0,int.from_bytes(struct.pack('<d',fraction),'little'));m.reg_write(UC_X86_REG_RIP,0x14007d5bc);return
        sp=m.reg_read(UC_X86_REG_RSP)
        if a in [0x1400eb010,0x1400eb850]:
            c=char(m.reg_read(UC_X86_REG_RCX));m.reg_write(UC_X86_REG_EAX,len(c.encode('utf-8'))if a==0x1400eb010 else ord(c))
        elif a==0x14007fc30:sourceRect=[signed(m.reg_read(r))for r in [UC_X86_REG_ECX,UC_X86_REG_EDX,UC_X86_REG_R8D,UC_X86_REG_R9D]];m.reg_write(UC_X86_REG_EAX,42)
        elif a==0x140080f40:c=char(m.reg_read(UC_X86_REG_RSI));calls.append(dict(codePoint=ord(c),source=sourceRect,position=[signed(m.reg_read(UC_X86_REG_ECX)),signed(m.reg_read(UC_X86_REG_EDX))]))
        m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x14007d4d0,0x14007d5b6,0x1400eb010,0x1400eb850,0x14007fc30,0x140080f40,0x14007f9c0]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    current=None
    for index,c in enumerate(cases):
        if current!=c['stem']:
            current=c['stem'];glyphs={};directory=ROOT/'runtimes/th06nc/artifacts/fonts'
            for line in (directory/f'advance_{current}.txt').read_text().splitlines():
                if line:cp,advance=line.split('\t');glyphs[int(cp,16)]=dict(advance=float(advance),source=[0,0,0,0])
            atlas=json.loads((directory/f'{current}.json').read_bytes())
            for frame in atlas['frames']:
                cp=int(frame['filename'],16);g=glyphs.setdefault(cp,dict(advance=0));r=frame['frame'];g['source']=[r['x'],r['y'],r['w'],r['h']]
        m.mem_write(n.assets,c['text'].encode('utf-8')+b'\0');sp=n.stack+0x8000;m.mem_write(sp+0x40,struct.pack('<2i',*c['origin']));m.mem_write(sp+0x60,struct.pack('<Q',n.vm+0x7000));m.mem_write(n.vm+0x7000,bytes(16));m.mem_write(n.owner+0x28,struct.pack('<i',55));calls.clear()
        for reg,value in [(UC_X86_REG_RSP,sp),(UC_X86_REG_RSI,n.assets),(UC_X86_REG_EBX,c['origin'][1]&0xffffffff),(UC_X86_REG_R13,n.owner)]:m.reg_write(reg,value)
        m.emu_start(0x14007d455,0x14007d624,count=10000000);assert calls==c['glyphs'],(index,c['stem'],'glyphs',calls[:3],c['glyphs'][:3]);metrics=list(struct.unpack('<4i',m.mem_read(n.vm+0x7000,16)));assert metrics==c['metrics'],(index,c['stem'],'metrics',metrics,c['metrics']);digest.update(json.dumps(dict(glyphs=calls,metrics=metrics),sort_keys=True).encode())
    assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha
    report=dict(scope=__doc__,fonts=len(set(c['stem']for c in cases)),cases=len(cases),glyphBlits=sum(len(c['glyphs'])for c in cases),stateSha256=digest.hexdigest(),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-font-layout-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
