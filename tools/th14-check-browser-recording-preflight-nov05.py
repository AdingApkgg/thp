"""Apply unchanged first1200 state/camera/VM/combat gates to browser slot02."""
from pathlib import Path
import hashlib
R=Path(__file__).resolve().parents[1]
parent=R/'tools/th14-check-player-pump-preflight-nov05.py';raw=parent.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='cca18110a22820dc1cb3a9b20f77250083ebeb63cfbdc51bc0498c13cd01f61e'
s=raw.decode()
for before,after in [("H=R/'artifacts/th14/script-rng-read-generation-nov05'","H=R/'artifacts/th14/browser-recording-native-nov05'"),
    ("D=H/'preflight-player-pump'","D=H/'preflight'"),
    ("H/'observer-player-pump/prepared.json'","H/'observer/prepared.json'"),
    ("H/'observer-player-pump/observer.py'","H/'observer/observer.py'"),
    ('artifacts/th14/native-campaign-assets/57d84a5cbe82-c48412a95f0f','artifacts/th14/native-campaign-assets/57d84a5cbe82-ec04b9bea043')]:
    assert s.count(before)==1,(before,s.count(before));s=s.replace(before,after)
exec(compile(s,str(__file__),'exec'),dict(__name__='__main__',__file__=str(__file__)))
