"""Retain the existing 1200-callback gates for the read-only slot profile."""
from pathlib import Path
import gzip,hashlib,json,struct
R=Path(__file__).resolve().parents[1]
parent=R/'tools/th14-check-player-pump-preflight-nov05.py';raw=parent.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='cca18110a22820dc1cb3a9b20f77250083ebeb63cfbdc51bc0498c13cd01f61e'
source=raw.decode()
for before,after in [("H=R/'artifacts/th14/script-rng-read-generation-nov05'","H=R/'artifacts/th14/shot-lifetime-native-nov05'"),
    ("D=H/'preflight-player-pump'","D=H/'preflight-slots-v2'"),
    ("H/'observer-player-pump/prepared.json'","H/'observer-slots-v2/prepared.json'"),
    ("H/'observer-player-pump/observer.py'","H/'observer-slots-v2/observer.py'")]:
    assert source.count(before)==1;source=source.replace(before,after)
exec(compile(source,str(__file__),'exec'),dict(__name__='__main__',__file__=str(__file__)))
home=R/'artifacts/th14/shot-lifetime-native-nov05/preflight-slots-v2'
index=json.loads((home/'native/shot-lifetime-index.json').read_bytes())
assert index['readOnly'] and [x['callback']for x in index['snapshots']]==[1,1000]
states=(home/'native/selected-state.u32').read_bytes()
for item in index['snapshots']:
    blob=(home/'native/shot-lifetime'/item['file']).read_bytes()
    assert len(blob)==item['bytes'] and hashlib.sha256(blob).hexdigest()==item['sha256']
    capture=json.loads(gzip.decompress(blob));pool=bytes.fromhex(capture['shotPoolRawHex'])
    assert len(pool)==256*0xd0
    expected=struct.unpack_from('<32I',states,(item['callback']-1)*128)
    assert capture['selected32']==list(expected)
    active=[i for i in range(256)if struct.unpack_from('<I',pool,i*0xd0+0x98)[0]]
    assert active==capture['activeSlots'] and len(active)==expected[26]
    for slot,vm in capture['vms'].items():
        raw=bytes.fromhex(vm['rawHex']);assert len(raw)==0x5cc
        assert struct.unpack_from('<I',raw,0x540)[0]==vm['handle']
        assert struct.unpack_from('<I',pool,int(slot)*0xd0+0x14)[0]==vm['handle']
verified=json.loads((home/'verified.json').read_bytes())
verified.update(nativeShotSnapshotsVerified=True,nativeShotSnapshots=len(index['snapshots']))
(home/'verified.json').write_text(json.dumps(verified,indent=2)+'\n')
print(json.dumps(dict(nativeShotSnapshotsVerified=True,snapshots=len(index['snapshots']))))
