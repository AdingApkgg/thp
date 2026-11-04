"""Use the existing bounded lifecycle runner with the fixed-watch profile."""
from pathlib import Path
import hashlib
R=Path(__file__).resolve().parents[1]
parent=R/'tools/th14-run-player-pump-observer-nov05.py';raw=parent.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='bbc8748f71754ba2226ece2ac68c723178f9f3a338621ab34afb0ed505906a15'
source=raw.decode();old="H=R/'artifacts/th14/script-rng-read-generation-nov05'";assert source.count(old)==1
source=source.replace(old,"H=R/'artifacts/th14/supervisor-pass-rng-nov05'")
source=source.replace("choices=['player-pump'],default='player-pump'","choices=['fixed'],default='fixed'")
old="H/('observer-'+a.profile)";assert source.count(old)==2
source=source.replace(old,"H/'observer-fixed-target'")
old='a=p.parse_args()';assert source.count(old)==1
source=source.replace(old,"p.add_argument('--startup-retry',action='store_true');a=p.parse_args()")
old="    out=H/(a.case+'-'+a.profile);assert not out.exists()";assert source.count(old)==1
source=source.replace(old,"""    if a.startup_retry:
        assert a.case=='prefix','Only the terminal zero-Player prefix startup can be retried'
        failure=json.loads((H/'prefix-fixed/native/report.json').read_bytes())
        ended=json.loads((H/'prefix-fixed/process-end.json').read_bytes())
        assert failure['childExited']and not failure['callbacks']and not failure['debugErrors']
        assert failure['error']==\"TimeoutError('Declared no-first-Player startup deadline exceeded')\"
        assert not failure['scriptRngAccessWatchArmed']and not failure['supervisorPassBoundaryEvents']and ended['guardStop']is None
        assert failure['sourceSha256']==SHA((H/'observer-fixed-target/observer.py').read_bytes())
    out=H/(a.case+'-'+a.profile+('-startup-retry1'if a.startup_retry else''));assert not out.exists()""")
# Resolve this file as the runner provenance; process/storage/exception controls
# retain the same implementation and finite preflight-before-prefix rule.
exec(compile(source,str(__file__),'exec'),dict(__name__='__main__',__file__=str(__file__)))
