"""Compare the 303 canonical live VM words at an actual title Present.

The native side is a read-only ordinary/overlay registry snapshot. The C++
side calls production Application and walks its live registries. A negative
comparison is saved before the command exits unsuccessfully.
"""
from pathlib import Path
import argparse,hashlib,json,struct

ROOT=Path(__file__).resolve().parents[1]


def native_words(row,by_address):
    raw=bytes.fromhex(row['rawVmHex']);assert len(raw)==0x5cc
    def w(at):return struct.unpack_from('<I',raw,at)[0]
    def handle(address):
        assert not address or address in by_address
        return by_address[address]if address else 0
    flags=w(0x18)
    offsets=[0x534,0x538,0x24,0x1c,0x548,0x54c,0x550,0x55c,0x560,0x564,
        0x3c,0x40,0x44,0x48,0x4c,0x50,0x54,0x58,0x5c,0x60,0x64,
        0x68,0x6c,0x78,0x7c,0x88,0x8c,0x3d8,0x3dc,0x80,0x84,
        *range(0x3b8,0x3d8,4),*range(0x4ac,0x4cc,4)]
    fields=['handle','file','script','timerPrevious','timerCurrent','timerFraction','pendingInterrupt','ageCurrent',
        'visible','drawingMode',*[f'nativeVmWord0x{x:x}'for x in offsets],
        'scriptInstructionOffset','worldX','worldY','worldZ','vertexColorMode','blendMode','depthDisabled',
        'flipX','flipY','anchorX','anchorY','addressV','cameraFollow','extraFloat0','extraFloat1','extraFloat2',
        'extraInt0','extraInt1','randomScale0','randomScale1','randomBound','scaleVelocityX','scaleVelocityY']
    values=[*[row[name]for name in fields[:8]],flags&1,(flags>>25)&31,*[w(at)for at in offsets],
        (w(0x28)-w(0x38))&0xffffffff if w(0x28)else 0xffffffff,
        *[w(at)for at in (0x59c,0x5a0,0x5a4)],(flags>>17)&3,(flags>>5)&15,
        int(bool(flags&0x2000)),int(bool(flags&0x800)),int(bool(flags&0x1000)),(flags>>21)&3,
        (flags>>23)&3,flags>>30,int(bool(flags&0x8000)),
        *[w(at)for at in (0x4cc,0x4d0,0x4d4,0x4d8,0x4dc,0x4e0,0x4e4,0x4e8,0x70,0x74)]]
    assert len(fields)==len(values)==80
    definitions=[('position',0x9c,3),('color',0xf4,3),('alpha',0x14c,1),('rotation',0x17c,3),
        ('scale',0x204,2),('color2',0x2d0,3),('alpha2',0x328,1),('scrollX',0x358,1),
        ('scrollY',0x388,1),('extraScale',0x248,2),('textureScale',0x28c,2)]
    for name,base,count in definitions:
        fields.extend(f'{name}.{group}{i}'for group in ('start','end','initialTangent','finalTangent')for i in range(count))
        fields.extend(f'{name}.{item}'for item in ('timerPrevious','timerCurrent','timerFraction','timerFlags','duration','mode'))
        values.extend(w(at)for at in [*range(base,base+4*count*4,4),*[base+5*count*4+x for x in (0,4,8,16,20,24)]])
    assert len(fields)==len(values)==234
    fields.extend(['childX','childY','childZ','pivotX','pivotY','slowdown','parentHandle','timerFlags','ageFlags',
        *[f'{name}{i}'for name in ('spriteMatrix','transformMatrix','uvMatrix')for i in range(16)]])
    values.extend([*[w(at)for at in (0x4ec,0x4f0,0x4f4,0x90,0x94,0x598)],handle(w(0x594)),
        w(0x558),w(0x56c),*[w(at)for at in range(0x3e0,0x4a0,4)]])
    fields.extend(['registryNextHandle','registryPreviousHandle','childNextHandle','childPreviousHandle'])
    values.extend(handle(w(at)-(0x570 if i<2 else 0x580))if w(at)else 0
        for i,at in enumerate((0x574,0x578,0x584,0x588)))
    fields.extend(['savedTimerPrevious','savedTimerCurrent','savedTimerFraction','savedTimerRatePresent',
        'savedTimerFlags','savedInstructionOffset','spriteFrame','inheritedColorCache'])
    values.extend([w(0),w(4),w(8),int(bool(w(12))),w(16),
        (w(20)-w(0x38))&0xffffffff if w(20)else 0xffffffff,w(0x4a4),w(0x53c)])
    assert len(fields)==len(values)==303
    return fields,values


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--native',type=Path,required=True);p.add_argument('--port',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    native_home=a.native.resolve();port_home=a.port.resolve();output=a.output.resolve()
    assert all(path.is_relative_to(ROOT/'artifacts/th14')for path in (native_home,port_home,output))
    nraw=(native_home/'live-vms-before-readback.json').read_bytes();native=json.loads(nraw)
    nr=json.loads((native_home/'report.json').read_text());pr=json.loads((port_home/'report.json').read_text())
    assert nr['childExited']and nr['frameReadbackCompleted']and not nr['error']and pr['completed']and not pr['error']
    assert native['readOnly']and native['readBeforeDiagnosticCalls']and native['ordinaryAndOverlayRegistryWalk']
    assert len(pr['captures'])==1;capture=pr['captures'][0]
    snapshot=next(row for row in nr['rows']if row.get('kind')=='native-Present-entry'and row['ordinal']==native['presentOrdinal'])
    observed=capture['referenceState'];rng=struct.unpack('<HHIHHI',bytes.fromhex(snapshot['rngHex']))
    assert observed[:7]==[snapshot['originalInitialTicks'],snapshot['originalProcessCookie'],snapshot['idleCounter'],rng[0],rng[2],rng[3],rng[5]]
    raw=(port_home/capture['liveAnimations']['file']).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==capture['liveAnimations']['sha256'];portable=json.loads(raw)
    assert portable['complete']and portable['comparedValues']==303
    by_address={struct.unpack_from('<I',bytes.fromhex(row['rawVmHex']),0x570)[0]:row['handle']for row in native['rows']}
    by_id={row[0]:row for row in portable['rows']};native_ids={row['handle']for row in native['rows']}
    assert len(by_id)==len(portable['rows'])and len(native_ids)==len(native['rows'])
    differences=[];fields=[]
    for row in native['rows']:
        fields,words=native_words(row,by_address);other=by_id.get(row['handle'])
        if other is None:differences.append(dict(handle=row['handle'],missingInPortable=True));continue
        assert len(other)==303
        for field,left,right in zip(fields,words,other):
            if left!=right:differences.append(dict(handle=row['handle'],file=row['file'],script=row['script'],field=field,native=left,portable=right))
    differences.extend(dict(handle=handle,extraInPortable=True)for handle in by_id if handle not in native_ids)
    order=[row['handle']for row in native['rows']]==[row[0]for row in portable['rows']]
    exact=not differences and order and len(native['rows'])==portable['expected']
    report=dict(allLiveValuesEqual=exact,registryOrderEqual=order,nativeCount=len(native['rows']),portableCount=len(portable['rows']),
        portableExpected=portable['expected'],comparedWordsPerVm=303,fields=fields,differenceCount=len(differences),differences=differences,
        nativeSnapshotSha256=hashlib.sha256(nraw).hexdigest(),portableSnapshotSha256=hashlib.sha256(raw).hexdigest(),
        nativePresent=native['presentOrdinal'],titleIdle=snapshot['idleCounter'],externalInputsAndSelectedRngEqual=True,
        sourceSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),completeGame=False,nativeEquivalent=False,browserAcceptance=False)
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items()if k not in ('fields','differences')}))
    if not exact:raise SystemExit(1)


if __name__=='__main__':main()
