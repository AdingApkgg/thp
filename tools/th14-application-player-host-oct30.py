"""Run the frozen real Application host with a bounded read-only Player dump.

The base host's clock, SDL, graphics, audio and file services remain unchanged.
The expanded host source is retained in each run alongside its exact hash.
"""
from pathlib import Path
import hashlib
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'tools/th14-native-application-process-host-oct27.py'
raw=base.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='80911b84ade035edef38e96a74a6c5cd0e3d8e3a4f09538475940ff256e9762c'
source=raw.decode('utf8').replace('\r\n','\n')
assert source.count('tool_raw=Path(__file__).read_bytes()')==1
source=source.replace('tool_raw=Path(__file__).read_bytes()','tool_raw=__th14_expanded_host_source_bytes')
needle=' def report():\n  result=dict('
assert source.count(needle)==1
replacement=''' def report():
  assert 'component_player_observations'in api,'Read-only Player adapter required'
  pointer=api['component_player_observations'](store)
  count,width,overflow,existing_hook=struct.unpack('<4I',mem.read(store,pointer,pointer+16))
  assert width==34 and count<=32768 and not overflow and not existing_hook
  player_raw=bytes(mem.read(store,pointer+16,pointer+16+count*width*4))
  assert len(player_raw)==count*width*4
  (O/'player-observations.u32').write_bytes(player_raw)
  player_observation=dict(rows=count,width=width,sha256=sha(player_raw),readOnly=True,gameplayStateOrHostInputsReplaced=False)
  result=dict('''
source=source.replace(needle,replacement)
needle="  result['applicationTicks']=application_ticks"
assert source.count(needle)==1
source=source.replace(needle,needle+"\n  result['beforePlayerObservation']=player_observation")
exec(compile(source,str(base),'exec'),{'__name__':'__main__','__file__':str(Path(__file__).resolve()),'__th14_expanded_host_source_bytes':source.encode('utf8')})
