"""Full original 2bac0 ending update with real seven script streams.

Every tick compares the complete 1280 owner hash; final queue and ordered
requests compare. Real dispatch, wait clocks, input acceleration, script replace
and integer helper execute. Dictionary/line splitting, deque/string storage,
ANM/font publication, background/music and allocator/free are controlled services.
No claim of native string-library, glyph/GPU/audio or application lifecycle parity.
"""
import ctypes,hashlib,json,struct,subprocess,sys
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    with_draw='--draw'in sys.argv;sources=['shared/th06nc/'+s+'.mjs'for s in ['ending-update','ending-command','ending-stream','ending-init']+(['ending-draw']if with_draw else [])];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources};script=r"""
import{readFileSync,readdirSync}from'node:fs';import{createHash}from'node:crypto';import{advanceEnding}from'./shared/th06nc/ending-update.mjs';import{drawEnding}from'./shared/th06nc/ending-draw.mjs';import{replaceEndingScript}from'./shared/th06nc/ending-init.mjs';
const home='runtimes/th06nc/artifacts/scripts/th06ED.dat',names=readdirSync(home).filter(n=>n.endsWith('.end')),scripts=Object.fromEntries(names.map((name,i)=>[name,{raw:readFileSync(home+'/'+name),base:0x70000000+i*0x4000}])),localization={};names.push('fixture.end');scripts['fixture.end']={raw:new Uint8Array([...new TextEncoder().encode('KEY_MULTI'),0,10,64,114,51,0,49,0,10,64,122,10,0]),base:0x7001c000,synthetic:true};localization.KEY_MULTI='one\n\nthree\n';for(const {raw}of Object.values(scripts))for(const key of new TextDecoder().decode(raw).match(/ED_[A-Z0-9_]+/g)??[])localization[key]=key+' α';for(const key of ['ED_END00B_05','ED_END10B_05'])localization[key]='replacement';
const hex=b=>Buffer.from(b).toString('hex'),sha=b=>createHash('sha256').update(b).digest('hex'),cases=[];
for(const name of names)for(const mode of ['plain','confirm','skip']){const first=scripts[name],bytes=new Uint8Array(0x1280),v=new DataView(bytes.buffer),state={bytes,script:first.raw,scriptBase:first.base,textQueue:[]},events=[],cleared=new Uint8Array(96);cleared[13]=99;v.setBigUint64(8,BigInt(first.base),true);v.setBigUint64(0x1250,BigInt(first.base),true);v.setBigUint64(0x1278,0x73008000n,true);v.setInt32(0x18,8,true);v.setInt32(0x1258,-999,true);v.setInt32(0x1260,-999,true);v.setUint8(0x124c,Number(mode==='skip'));const initial=hex(bytes),services={cleared,loadBackground:path=>{events.push({kind:'background',path});return 0;},bindAnm:(offset,id)=>events.push({kind:'anm',offset,id}),bindSprite:(offset,id)=>events.push({kind:'sprite',offset,id}),playMusic:path=>events.push({kind:'music',path}),fadeMusic:value=>events.push({kind:'fade',value}),prepareText:(offset,id)=>events.push({kind:'prepare',offset,id}),publishText:r=>events.push({kind:'publish',...r}),tickAnm:offset=>events.push({kind:'tick',offset}),switchScript:path=>{const result=replaceEndingScript(bytes,path,{loadScript:path=>{events.push({kind:'load',path});const next=scripts[path.split('/').at(-1)];if(!next)return 0n;state.script=next.raw;state.scriptBase=next.base;return BigInt(next.base);},freeScript:pointer=>events.push({kind:'free',pointer:Number(pointer)}),reportError:key=>events.push({kind:'error',key})});return result;}};const frames=[];let previous=0,result=1;for(let frame=0;result!==0&&frame<100000;frame++){const held=mode==='skip'?8:mode==='confirm'&&frame%20===0?256:0;try{result=advanceEnding(state,{held,previous,lifeProtection:mode==='confirm',localization},services);}catch(error){throw Error(JSON.stringify({name,mode,frame,cursor:String(v.getBigUint64(0x1250,true)),line:v.getInt32(0x1270,true),queue:state.textQueue,last:events.slice(-3)}),{cause:error});}if(withDraw&&result!==0)drawEnding(bytes,{}, {drawVm:(offset,args)=>events.push({kind:'drawVm',offset,args}),drawFade:r=>events.push({kind:'drawFade',...r})});frames.push({held,previous,result,sha256:sha(bytes)});previous=held;}if(result!==0)throw Error('Ending fixture failed to terminate '+name+'/'+mode);cases.push({name,mode,initial,cleared:hex(cleared),frames,queue:state.textQueue,events});}
console.log(JSON.stringify({scripts:Object.fromEntries(Object.entries(scripts).map(([name,x])=>[name,{base:x.base,raw:hex(x.raw),synthetic:Boolean(x.synthetic)}])),localization,cases}));
"""
    script='const withDraw='+json.dumps(with_draw)+';'+script;generated=subprocess.run(['node','--input-type=module','-e',script],cwd=ROOT,capture_output=True);assert generated.returncode==0,generated.stderr.decode(errors='replace')[-2200:];data=json.loads(generated.stdout);n=Native();m=n.m;atoi=ctypes.CDLL('ucrtbase').atoi;atoi.argtypes=[ctypes.c_char_p];atoi.restype=ctypes.c_int;queue=[];events=[];queueptr=n.vm+0x8000;stringptr=n.vm+0x9000;chars=n.vm+0xa000;cookie=0x1402bcf20;life=False
    for name,d in data['scripts'].items():
        m.mem_write(d['base'],bytes.fromhex(d['raw'])+bytes(32));
        if d.get('synthetic'):continue
        p='runtimes/th06nc/artifacts/scripts/th06ED.dat/'+name;hashes[p]=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
    def cstring(p):return bytes(m.mem_read(p,4096)).split(b'\0')[0]
    def popcount():m.mem_write(queueptr+0x20,struct.pack('<Q',len(queue)))
    def ret(m):
        sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    def hook(m,a,size,u):
        sp=m.reg_read(UC_X86_REG_RSP)
        if a==0x14002c35a:
            key=cstring(m.reg_read(UC_X86_REG_RDI)).decode();text=data['localization'].get(key,key)
            if text:
                lines=text.split('\n')
                if text.endswith('\n'):lines.pop()
                queue.extend(lines)
            popcount();m.reg_write(UC_X86_REG_RIP,0x14002c4f6);return
        if a==n.vm+0x7000:m.reg_write(UC_X86_REG_EAX,atoi(cstring(m.reg_read(UC_X86_REG_RCX)))&0xffffffff)
        elif a==0x1402be089:m.reg_write(UC_X86_REG_EAX,0 if cstring(m.reg_read(UC_X86_REG_RCX))==cstring(m.reg_read(UC_X86_REG_RDX))else 1)
        elif a==0x14002ddb0:
            raw=queue[0].encode();m.mem_write(chars,raw+b'\0');m.mem_write(stringptr,struct.pack('<4Q',chars,0,len(raw),max(16,len(raw))));m.reg_write(UC_X86_REG_RAX,stringptr)
        elif a==0x14002daf0:queue.pop(0);popcount()
        elif a==0x140008210:
            dst=m.reg_read(UC_X86_REG_RCX);m.mem_write(dst,bytes(m.mem_read(m.reg_read(UC_X86_REG_RDX),32)));m.reg_write(UC_X86_REG_RAX,dst)
        elif a==0x140008400:m.reg_write(UC_X86_REG_RAX,struct.unpack('<Q',m.mem_read(m.reg_read(UC_X86_REG_RCX),8))[0])
        elif a==0x140002a20:
            offset=m.reg_read(UC_X86_REG_RDX)-n.owner;events.append(dict(kind='prepare',offset=offset,id=struct.unpack('<H',m.mem_read(n.owner+offset+0x38,2))[0]))
        elif a==0x140007530:
            offset=m.reg_read(UC_X86_REG_RDX)-n.owner;textptr=struct.unpack('<Q',m.mem_read(sp+0x38,8))[0];events.append(dict(kind='publish',offset=offset,id=struct.unpack('<H',m.mem_read(n.owner+offset+0x38,2))[0],text=cstring(textptr).decode(),color=m.reg_read(UC_X86_REG_R8)&0xffffffff,colors=[m.reg_read(UC_X86_REG_R9)&0xffffffff,struct.unpack('<I',m.mem_read(sp+0x28,4))[0],struct.unpack('<I',m.mem_read(sp+0x30,4))[0]]))
        elif a==0x140002a80:events.append(dict(kind='drawVm',offset=m.reg_read(UC_X86_REG_RDX)-n.owner,args=[m.reg_read(UC_X86_REG_R8)&0xffffffff,m.reg_read(UC_X86_REG_R9)&255,bytes(m.mem_read(sp+0x28,1))[0]]))
        elif a==0x140075be0:events.append(dict(kind='drawFade',rect=list(struct.unpack('<4f',m.mem_read(m.reg_read(UC_X86_REG_RCX),16))),color=m.reg_read(UC_X86_REG_RDX)&0xffffffff))
        elif a==0x1400069b0:events.append(dict(kind='tick',offset=m.reg_read(UC_X86_REG_RDX)-n.owner))
        elif a==0x1402bdee2:
            dst=m.reg_read(UC_X86_REG_RCX);m.mem_write(dst,bytes([m.reg_read(UC_X86_REG_RDX)&255])*m.reg_read(UC_X86_REG_R8));m.reg_write(UC_X86_REG_RAX,dst)
        elif a==0x140007620:events.append(dict(kind='background',path=cstring(m.reg_read(UC_X86_REG_R8)).decode()));m.reg_write(UC_X86_REG_EAX,0)
        elif a in [0x140002760,0x140002980]:events.append(dict(kind='anm'if a==0x140002760 else'sprite',offset=m.reg_read(UC_X86_REG_RDX)-n.owner,id=m.reg_read(UC_X86_REG_R8)&0xffffffff))
        elif a==0x14007bc80:events.append(dict(kind='music',path=cstring(m.reg_read(UC_X86_REG_RDX)).decode()))
        elif a==0x14007c000:events.append(dict(kind='fade',value=struct.unpack('<f',struct.pack('<I',m.reg_read(UC_X86_REG_XMM1)&0xffffffff))[0]))
        elif a==0x1400387a0:
            path=cstring(m.reg_read(UC_X86_REG_RCX)).decode();events.append(dict(kind='load',path=path));d=data['scripts'].get(path.split('/')[-1]);m.reg_write(UC_X86_REG_RAX,d['base']if d else 0)
        elif a==n.vm+0x7010:events.append(dict(kind='free',pointer=m.reg_read(UC_X86_REG_RCX)))
        elif a==0x140039ef0:events.append(dict(kind='error',key='endingFileLoadFailed'))
        ret(m)
    m.mem_write(0x1402c0328,struct.pack('<Q',n.vm+0x7000));m.mem_write(0x1402c0378,struct.pack('<Q',n.vm+0x7010));m.mem_write(0x140a6e9b0,struct.pack('<Q',n.manager));m.mem_write(n.manager+0x22f90,struct.pack('<2i',-1,-1));m.mem_write(0x140c21e3c,struct.pack('<4i',0,0,854,480))
    addresses=[0x14002c35a,n.vm+0x7000,n.vm+0x7010,0x1402be089,0x14002ddb0,0x14002daf0,0x140008210,0x140008400,0x140008410,0x140002a20,0x140007530,0x1400069b0,0x1402bdee2,0x140007620,0x140002760,0x140002980,0x14007bc80,0x14007c000,0x1400387a0,0x140039ef0,0x140002a80,0x140075be0,cookie]
    for a in addresses:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    digest=hashlib.sha256();ticks=0
    for index,c in enumerate(data['cases']):
        m.mem_write(n.owner,bytes.fromhex(c['initial']));m.mem_write(0x1404ff0f4,bytes.fromhex(c['cleared']));life=c['mode']=='confirm';m.mem_write(0x1404f27c4,bytes([life]));queue.clear();events.clear();popcount()
        for frame,f in enumerate(c['frames']):
            m.mem_write(0x140a6ec60,struct.pack('<2I',f['held'],f['previous']));sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.emu_start(0x14002bac0,n.stack+0xf000,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000,(index,frame,'stop');result=m.reg_read(UC_X86_REG_EAX);assert result==f['result'],(index,frame,'return')
            if with_draw and result!=0:
                m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.emu_start(0x14002c600,n.stack+0xf000,count=100000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000,(index,frame,'draw stop')
            actual=bytes(m.mem_read(n.owner,0x1280));assert hashlib.sha256(actual).hexdigest()==f['sha256'],(index,c['name'],c['mode'],frame,'owner');digest.update(actual);ticks+=1
        assert queue==c['queue'],(index,'queue');assert events==c['events'],(index,'requests',next(((j,a,b)for j,(a,b)in enumerate(zip(events,c['events']))if a!=b),('counts',len(events),len(c['events']))))
    assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in hashes}
    report=dict(scope=__doc__+('\nWith --draw, each nonterminal update is followed by the original draw callback with no background handles. This explicit coordinator compares combined owner mutations and draw requests, not the native application task-registration/lifecycle.'if with_draw else''),cases=len(data['cases']),ticks=ticks,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/('docs/porting/th06nc-ending-update-draw-native-verified.json'if with_draw else'docs/porting/th06nc-ending-update-native-verified.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'cases':len(data['cases']),'ticks':ticks}))
if __name__=='__main__':main()
