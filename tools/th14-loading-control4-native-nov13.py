"""Extend the pinned loading/control oracle with the observed flags4 state."""
from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parents[1]
parent = ROOT / 'tools/th14-loading-control-native-nov11.py'
assert hashlib.sha256(parent.read_bytes()).hexdigest() == 'a7b3f353c8b5ee32032f90d9e65abc4efc22bc72d9276b53b7ca2bb368c1f7eb'
source = parent.read_text()
start = source.index('        for case in [')
stop = source.index('            handle = reset', start)
source = source[:start] + '''        for case in [
            dict(name='flags4-finish-while-set', rate=1., frozenFlags=4, initialFlags=4, freezeBegin=0, freezeEnd=84, finishBeforeUpdate=40, frames=160),
            dict(name='flags4-clear-and-finish', rate=1., frozenFlags=4, initialFlags=4, freezeBegin=0, freezeEnd=80, finishBeforeUpdate=80, frames=160),
            dict(name='flags4-clear-before-finish', rate=1., frozenFlags=4, initialFlags=4, freezeBegin=0, freezeEnd=80, finishBeforeUpdate=84, frames=160),
            dict(name='flags4-finish-before-clear', rate=1., frozenFlags=4, initialFlags=4, freezeBegin=0, freezeEnd=84, finishBeforeUpdate=80, frames=160),
            dict(name='flags4-late-publication', rate=1., frozenFlags=4, initialFlags=0, freezeBegin=76, freezeEnd=84, finishBeforeUpdate=84, frames=160),
            dict(name='flags4-half-rate', rate=.5, frozenFlags=4, initialFlags=4, freezeBegin=0, freezeEnd=80, finishBeforeUpdate=84, frames=160),
        ]:
            finish, frames = case['finishBeforeUpdate'], case['frames']
''' + source[stop:]
changes = {
    '    def reset(rate):\n        put(control + 0x80, 0)': '    def reset(rate, initial_flags):\n        put(control + 0x80, initial_flags)',
    "            handle = reset(case['rate'])": "            handle = reset(case['rate'], case['initialFlags'])",
    "            record = dict(**case, finishBeforeUpdate=finish, frames=frames,\n                          freezeBegin=20, freezeEnd=60, byteOffset=stream.tell(), rootHandle=handle)":
        '            record = dict(**case, byteOffset=stream.tell(), rootHandle=handle)',
    "case['frozenFlags'] if 20 <= frame < 60 else 0": "case['frozenFlags'] if case['freezeBegin'] <= frame < case['freezeEnd'] else 0",
}
for old, new in changes.items():
    assert source.count(old) == 1, old
    source = source.replace(old, new)
exec(compile(source, str(parent), 'exec'), globals())
