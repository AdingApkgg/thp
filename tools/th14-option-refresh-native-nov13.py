"""Extend real Player initialization through option factories and stage reset.

The original pool, ANM factories, resource templates, interpreter and registry
updates execute. The sequence of power values and ticks is a component input.
"""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1]
parent=R/'tools/th14-player-initialization-oracle-nov13.py'
proof=json.loads((R/'artifacts/th14/player-initialization-oracle-nov13/native.json').read_bytes())
assert hashlib.sha256(parent.read_bytes()).hexdigest()==proof['toolSha256']
source=parent.read_text()
source=source.replace("H = R / 'artifacts/th14/player-initialization-oracle-nov13'", "H = R / 'artifacts/th14/option-refresh-oracle-nov13'")
source=source.replace('def run(entry, owner):','def run(entry, owner, args=()):')
source=source.replace('            put(stack, end)','            m.mem_write(stack, struct.pack("<"+"I"*(len(args)+1),end,*args))')
needle='        rows.append(row)'
assert source.count(needle)==1
extra='''
        # Register the two real manager callbacks alongside disabled Player18.
        m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EBP,stack-0x100)
        put(stack-0x118,loader.manager)
        m.emu_start(0x47aa08,0x47aae5,count=100000)
        assert m.reg_read(UC_X86_REG_EIP)==0x47aae5
        sentinel=loader.manager+0xbc7af8
        vms=[loader.manager+0xdc+(8190-i)*0x5e4 for i in range(64)]
        for offset in [0xfe8208,0xfe820c,0xfe8210,0xfe8214,0xff52c8]:put(loader.manager+offset,0)
        m.mem_write(sentinel,bytes(16));put(sentinel+4,vms[0]+0x5cc)
        for i,vm in enumerate(vms):
            m.mem_write(vm,bytes(0x5e4));run(0x40cc90,vm)
            put(vm+0x5cc,vm);put(vm+0x5d0,vms[i+1]+0x5cc if i+1<len(vms)else 0)
            put(vm+0x5d4,vms[i-1]+0x5cc if i else sentinel);put(vm+0x5e0,8190-i)
        callbacks=[];hud=[]
        def observe(uc,pc,size,_):
            if pc in (0x47e7f0,0x47e7c0,0x44ec60):callbacks.append(pc)
            if pc==0x434ef0:
                sp=uc.reg_read(UC_X86_REG_ESP);hud.append([get(sp+4),get(sp+8)])
                uc.reg_write(UC_X86_REG_EAX,0);uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+12)
        for pc in [0x47e7f0,0x47e7c0,0x44ec60,0x434ef0]:m.hook_add(UC_HOOK_CODE,observe,begin=pc,end=pc)
        option_offsets=[0,0x54,0x58,0x5c,0x60,0x64,0x68,0x6c,0x70,0xa8,0xb0,0xb4,0xd0,0xd4,0xd8]
        stages=[]
        def capture(label):
            live=[]
            for offset in [0xfe8208,0xfe8210]:
                node=get(loader.manager+offset)
                while node:
                    vm=get(node);assert vm in vms,'Declared pool exhausted or unrelated VM'
                    assert vm not in live;live.append(vm);assert len(live)<=64;node=get(node+4)
            by_address={vm:get(vm+0x540)for vm in live};by_address[player+0x14]=0
            vm_words=[]
            for vm in live:
                raw=bytes(m.mem_read(vm,0x5cc))
                v=dict(rawVmHex=raw.hex(),handle=get(vm+0x540),file=struct.unpack_from('<H',raw,0x36)[0],
                       script=struct.unpack_from('<H',raw,0x4aa)[0],timerPrevious=get(vm+0x548),timerCurrent=get(vm+0x54c),
                       timerFraction=get(vm+0x550),pendingInterrupt=get(vm+0x4a0),ageCurrent=get(vm+0x560))
                _,words=serializer.native_words(v,by_address);vm_words+=words
            option_words=[get(player+0xd6ec+i*0xe4+offset)for i in range(8)for offset in option_offsets]
            rr=struct.unpack('<HHIHHI',m.mem_read(0x4db508,16))
            state=[get(player+offset)for offset in [0x684,0x18334,0x183a4,0x184b0]]
            clocks=[get(player+base+offset)if offset!=12 else int(bool(get(player+base+offset)))
                    for base in [0x68c,0x6a0,0x6b4,0x18338]for offset in [0,4,8,12,16]]
            history=[get(player+0x183a8+i*4)for i in range(66)]
            stages.append(dict(label=label,head=[len(live),rr[0],rr[2],rr[3],rr[5]],state=state,clocks=clocks,
                               options=option_words,history=history,vms=vm_words,hudCalls=len(hud)))
        put(0x4f5864,2);put(0x4f5868,0)
        sequence=[('refresh100',100,'refresh'),('tick1',100,'tick'),('repeat100',100,'refresh'),
                  ('activate100',100,'stage'),('tick2',100,'tick'),('grow300',300,'refresh'),('tick3',300,'tick'),
                  ('max400',400,'refresh'),('repeat400',400,'refresh'),('tick4',400,'tick'),
                  ('activate400',400,'stage'),('tick5',400,'tick'),('tick6',400,'tick'),('zero',0,'refresh'),('tick7',0,'tick')]
        for label,power,kind in sequence:
            put(0x4f5858,power)
            if kind=='refresh':run(0x44f970,player)
            elif kind=='stage':run(0x44cc10,player)
            else:
                callbacks.clear();run(0x401280,registry)
                assert callbacks==[0x47e7f0,0x47e7c0],callbacks
            capture(label)
        assert len(hud)==2 and hud==[[2,0],[2,0]]
        row['sequence']=[dict(label=label,power=power,kind=kind)for label,power,kind in sequence]
        row['optionOffsets']=option_offsets;row['stages']=stages;row['hudCalls']=hud
        row['realOptionFactoriesAndRegistryUpdates']=True;row['declaredPoolCapacity']=64
        print(json.dumps(dict(slot=slot,optionStages=len(stages),maxLiveVms=max(s['head'][0]for s in stages))),flush=True)
'''
source=source.replace(needle,extra+'\n'+needle)
exec(compile(source,str(parent),'exec'),globals())
