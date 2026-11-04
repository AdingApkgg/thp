"""Apply the existing finite preflight checks to the fixed-watch observer."""
from pathlib import Path
import hashlib
R=Path(__file__).resolve().parents[1]
parent=R/'tools/th14-check-player-pump-preflight-nov05.py';raw=parent.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='cca18110a22820dc1cb3a9b20f77250083ebeb63cfbdc51bc0498c13cd01f61e'
source=raw.decode()
for old,new in [("H=R/'artifacts/th14/script-rng-read-generation-nov05'","H=R/'artifacts/th14/supervisor-pass-rng-nov05'"),
                ("D=H/'preflight-player-pump'","D=H/'preflight-fixed'"),
                ("H/'observer-player-pump/prepared.json'","H/'observer-fixed-target/prepared.json'"),
                ("H/'observer-player-pump/observer.py'","H/'observer-fixed-target/observer.py'")]:
    assert source.count(old)==1;source=source.replace(old,new)
exec(compile(source,str(__file__),'exec'),dict(__name__='__main__',__file__=str(__file__)))
