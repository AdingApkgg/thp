"""Read-only original bullet-pool and spawn observations around one window."""
import hashlib, importlib, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ESP

RUN=importlib.import_module('th14-native-bootstrap-run');ROOT=RUN.ROOT
SHA=lambda b:hashlib.sha256(b).hexdigest()


def main():
    def take(name):
        i=sys.argv.index(name);v=sys.argv[i+1];del sys.argv[i:i+2];return v
    first,last=int(take('--entity-first')),int(take('--entity-last'))
    output=(ROOT/take('--entity-output')).resolve()
    assert 1<=first<=last and last-first<=200 and output.is_relative_to(ROOT/'artifacts/th14') and not output.exists()
    original,parent,observer=RUN.Uc,Path(RUN.__file__).read_bytes(),Path(__file__).read_bytes()
    frames,spawns=[],[]
    def constructor(*args,**kwargs):
        m=original(*args,**kwargs);get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
        def frame():
            ctl=get(0x4db558);return get(ctl+0x14) if ctl else 0
        def observed(uc,address,size,user):
            current=frame()
            if not first<=current<=last:return
            manager=get(0x4db530);bullets=[];node=get(manager+0x80);seen=set()
            while node and node not in seen:
                assert len(seen)<2000;seen.add(node);bullet=get(node)
                if bullet:
                    words=[get(bullet+off) for off in (0x20,0x24,0xbc0,0xbc4,0xbc8,0xbcc,0xbd0,0xbd4,0xbd8,0xbdc,0xbe0,0xbe4,0x13c4,0x13ec,0xc04)]
                    bullets.append([struct.unpack('<H',m.mem_read(bullet+0xc0e,2))[0],*words])
                node=get(node+4)
            frames.append(dict(stageFrame=current,bulletDetails=bullets))
        def spawned(uc,address,size,user):
            current=frame()
            if not first<=current<=last:return
            sp=uc.reg_read(UC_X86_REG_ESP);p=get(sp+4);name=bytearray()
            for i in range(128):
                c=bytes(uc.mem_read(p+i,1))[0]
                if not c:break
                name.append(c)
            else:raise RuntimeError('Unbounded original spawn name.')
            spawns.append(dict(stageFrame=current,name=name.decode('ascii'),caller=hex(get(sp)),descriptor=list(struct.unpack('<21I',uc.mem_read(get(sp+8),84))),enemyCountBefore=get(get(0x4db544)+0xd8)))
        m.hook_add(UC_HOOK_CODE,observed,begin=0x44dbd0,end=0x44dbd0)
        m.hook_add(UC_HOOK_CODE,spawned,begin=0x421ef0,end=0x421ef0)
        return m
    RUN.Uc=constructor
    try:RUN.main()
    finally:
        RUN.Uc=original;output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps(dict(diagnosticOnly=True,completeGame=False,nativeEquivalent=False,frames=frames,spawns=spawns,
            observerSha256=SHA(observer),parentSourceSha256=SHA(parent),
            scope='Read-only original executable bullet pool and real ECL spawn requests. Parent physical all64 comparison is separate; supplemental memory observations are not a new retail capture, candidate input or whole-game proof.'),indent=2)+'\n')
        output.with_suffix('.observer.py').write_bytes(observer);output.with_suffix('.parent.py').write_bytes(parent)


if __name__=='__main__':main()
