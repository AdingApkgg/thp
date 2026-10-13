"""Read-only late collision details using the existing owned retail debugger.

Only the capture-side observation window changes. Original executable code,
input, stock, RNG and clocks are untouched apart from the declared warm mode.
Existing capture tools remain immutable for historical source bindings.
"""
import hashlib, importlib, inspect, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda b: hashlib.sha256(b).hexdigest()


def main():
    observer_source = Path(__file__).read_bytes()
    def take(name):
        index = sys.argv.index(name)
        value = sys.argv[index+1]
        del sys.argv[index:index+2]
        return value
    first, last = int(take('--detail-first')), int(take('--detail-last'))
    assert 1 <= first <= last and last-first <= 500
    capture_fires = '--capture-fires' in sys.argv
    if capture_fires:
        sys.argv.remove('--capture-fires')
    output = (ROOT/sys.argv[sys.argv.index('--output')+1]).resolve()
    assert output.is_relative_to(ROOT/'artifacts/th14')
    capture = importlib.import_module('th14-native-session-capture')
    warm = importlib.import_module('th14-native-stored-stage-bootstrap-capture')
    original = inspect.getsource(capture.main)
    old = "if opt.bullet_details and row['stageFrame'] <= 350:"
    assert original.count(old) == 1
    source = original.replace(old, f"if opt.bullet_details and {first} <= row['stageFrame'] <= {last}:")
    marker = "            manager=u32(0x4db530);row['bulletDetails']=[]"
    assert source.count(marker) == 1
    source = source.replace(marker, """            row['collisionDiagnostic']={
                'playerFloatBits':[pu(0x5e0),pu(0x5e4)],
                'hitBoundsBits':[pu(off) for off in (0x630,0x634,0x63c,0x640)],
                'scaleFactorBits':pu(0x18308), 'scaleFlags':pu(0x182d4)}
"""+marker)
    # Add scale and stable pool slot to each captured bullet. No guest writes.
    needle="row['bulletDetails'].append([struct.unpack_from('<H',data,0xc0e)[0],"
    assert source.count(needle) == 1
    prefix="row.setdefault('bulletCollisionExtras',[]).append([bullet,*[word(off) for off in (0xbf8,0xbfc)]])\n                    "
    source = source.replace(needle,prefix+needle)
    if capture_fires:
        for old, new in (("row['selection']==[2,0,1,1]", "row['selection']==[2,0,1,5]"),
                         ('if frame<=350:',f'if {first}<=frame<={last}:')):
            assert source.count(old) == 1
            source = source.replace(old,new)
        old="exclusionBits=u32(u32(0x4db530)+0x60)))"
        assert source.count(old) == 1
        source = source.replace(old,"exclusionBits=u32(u32(0x4db530)+0x60),rateBits=u32(0x4d8f58)))")
    namespace = dict(capture.__dict__)
    exec(compile(source,str(Path(__file__))+'::capture-observer','exec'),namespace)
    prior = capture.main
    capture.main = namespace['main']
    if '--bullet-details' not in sys.argv:
        sys.argv.append('--bullet-details')
    if capture_fires:
        sys.argv.append('--fire-details')
    try:
        warm.main()
    finally:
        capture.main = prior
        if output.exists():
            report = json.loads(output.read_text())
            report['lateCollisionObserver'] = dict(first=first,last=last,
                originalCaptureMainSha256=SHA(original.encode()),
                instrumentedCaptureMainSha256=SHA(source.encode()),
                toolSha256=SHA(observer_source),fireObservationEnabled=capture_fires,
                scope='Capture-side memory reads only; no guest gameplay or input changes. Bullet addresses are diagnostic identities, not normalized object-equivalence fields.')
            output.write_text(json.dumps(report,indent=2)+'\n')
            (output.parent/'capture-observer-source.py').write_bytes(observer_source)


if __name__ == '__main__':
    main()
