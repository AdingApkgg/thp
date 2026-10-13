"""Read-only original-backend enemy health history; never candidate state input."""
import hashlib, importlib, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE

RUN=importlib.import_module('th14-native-bootstrap-run')
ROOT=RUN.ROOT
SHA=lambda b:hashlib.sha256(b).hexdigest()


def main():
    index=sys.argv.index('--health-output');output=(ROOT/sys.argv[index+1]).resolve();del sys.argv[index:index+2]
    assert output.is_relative_to(ROOT/'artifacts/th14') and not output.exists()
    output.parent.mkdir(parents=True,exist_ok=True)
    original,source=RUN.Uc,Path(RUN.__file__).read_bytes()
    observer=Path(__file__).read_bytes();count=0
    with output.open('w',encoding='utf-8') as stream:
        def constructor(*args,**kwargs):
            machine=original(*args,**kwargs)
            get=lambda p:struct.unpack('<I',machine.mem_read(p,4))[0]
            def observed(uc,address,size,user):
                nonlocal count
                manager,control=get(0x4db544),get(0x4db558)
                records=[];node=get(manager+0xd0) if manager else 0;seen=set()
                while node and node not in seen:
                    assert len(seen)<1000;seen.add(node);enemy=get(node)
                    if enemy:
                        body=enemy+0x11f0
                        records.append(dict(id=get(enemy+0x11e4),
                            health=[get(body+off) for off in (0x3f74,0x3f78,0x3f7c,0x3f80,0x3f84,0x3f8c)],
                            rawDamageTotal=get(body+0x3f88),
                            immunity=[get(body+off) for off in (0x3fec,0x3ff0,0x3ff4)],
                            phase=[get(body+off) for off in (0x2b8,0x2bc,0x2c0)],
                            position=[get(body+0x44),get(body+0x48)]))
                    node=get(node+4)
                stream.write(json.dumps(dict(index=count,stageFrame=get(control+0x14),enemies=records),separators=(',',':'))+'\n')
                stream.flush();count+=1
            machine.hook_add(UC_HOOK_CODE,observed,begin=0x44dbd0,end=0x44dbd0)
            return machine
        RUN.Uc=constructor
        try:RUN.main()
        finally:RUN.Uc=original
    output.with_suffix('.observer.py').write_bytes(observer)
    output.with_suffix('.parent.py').write_bytes(source)
    output.with_suffix('.json').write_text(json.dumps(dict(diagnosticOnly=True,completeGame=False,nativeEquivalent=False,
        frames=count,streamSha256=SHA(output.read_bytes()),observerSha256=SHA(observer),parentSourceSha256=SHA(source),
        scope='Read-only before-player health observations from the pinned original executable backend. No candidate inputs or guest-state writes. Supplemental object observations require retail-window anchoring; the parent all64 reference check remains separate.'),indent=2)+'\n')


if __name__=='__main__':main()
