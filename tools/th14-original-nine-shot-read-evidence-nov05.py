"""Bind the unchanged A-profile RNG decoder to the new readonly slot observer.

Composes the frozen register, rotating-pump and player/pump verifiers. Their
native event/arithmetic checks remain; only observer/preflight provenance and
the already declared A-profile DR0 mux binding differ from the base verifier.
"""
from pathlib import Path
import argparse
import hashlib
import json

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/original-nine-shot-native-nov05'
SHA = lambda data: hashlib.sha256(data).hexdigest()
OBSERVER = 'b9ecbcc089ee738d5fda9aa5bc453b3912f6d4b683a5626acf7785275c71d2f4'


def module(name, expected, transform, injected=None):
    path = R / 'tools' / name
    raw = path.read_bytes()
    assert SHA(raw) == expected
    source = transform(raw.decode())
    env = dict(__file__=str(Path(__file__).resolve()), __name__='sealed_slot_read_parent')
    env.update(injected or {})
    exec(compile(source, str(path), 'exec'), env)
    return env['verify']


def one(source, before, after):
    assert source.count(before) == 1, (before[:100], source.count(before))
    return source.replace(before, after)


def base_source(source):
    source = one(source, "H/'observer-pending-status/observer.py'",
                 "R/'artifacts/th14/original-nine-shot-native-nov05/observer-slots-v2/observer.py'")
    source = one(source, "H/'preflight-pending-status/verified.json'",
                 "R/'artifacts/th14/original-nine-shot-native-nov05/preflight-slots-v2/verified.json'")
    return one(source, '26727dd09ec942e04e9def563c5ec8b56e6a010912f44e4ed1b28809bb7ce596', OBSERVER)


def pump_source(source):
    first = source.index("    parent=R/'tools/th14-rng-register-trace-evidence-nov05.py'")
    last = source.index("    bindings=proof['bindings']", first)
    # The replaced prelude compiles/invokes a SHA-bound parent and substitutes
    # its observer bindings. Here that same parent was independently compiled
    # above with the declared slot bindings; no native checks are removed.
    source = source[:first] + "    parent=R/'tools/th14-rng-register-trace-evidence-nov05.py'\n    proof=base_verify(native)\n" + source[last:]
    source = one(source, "OBSERVER_SHA='4595cf23b509c917cf881aa420b5629307aacb7f07c793a51482e9b14b254754'", "OBSERVER_SHA='"+OBSERVER+"'")
    source = one(source, "prepared=load(H/'observer-rotating-pump/prepared.json')",
                 "prepared=load(R/'artifacts/th14/original-nine-shot-native-nov05/observer-slots-v2/prepared.json')")
    return one(source, "p['debugAddresses'][0]==0x44dbd0", "p['debugAddresses'][0]in (0x44dbd0,0x47d720)")


def mux_source(source):
    first = source.index("    parent=R/'tools/th14-rng-pump-trace-evidence-nov05.py'")
    last = source.index("    def blob(path):", first)
    source = source[:first] + "    parent=R/'tools/th14-rng-pump-trace-evidence-nov05.py'\n    proof=pump_verify(native);bindings=proof['bindings']\n" + source[last:]
    return one(source, "OBSERVER_SHA='f215b4fae98ac88c1cd94576f99ccb31484d157497cf14e7bfd89e22f79a8884'", "OBSERVER_SHA='"+OBSERVER+"'")


def verify(native):
    prep = json.loads((H / 'observer-slots-v2/prepared.json').read_bytes())
    assert prep['observerSha256'] == OBSERVER
    assert prep['parentObserverSha256'] == 'f215b4fae98ac88c1cd94576f99ccb31484d157497cf14e7bfd89e22f79a8884'
    assert prep['criticalMutationCallAstUnchanged'] and prep['hardwareWatchProfileUnchanged']
    assert prep['additionalGameMemoryWrites'] == prep['additionalSuspendsOrResumes'] == 0
    assert SHA((H / 'observer-slots-v2/observer.py').read_bytes()) == OBSERVER
    base = module('th14-rng-register-trace-evidence-nov05.py',
                  '1b4d904ca8e93b1b6bf6158639139426ea3297182006b9ec57fe6308085237dd', base_source)
    pump = module('th14-rng-pump-trace-evidence-nov05.py',
                  'bebd84d7e0bae59eec80a30e2183bcebcd164b94277f053105d56f996afbe73b',
                  pump_source, dict(base_verify=base))
    mux = module('th14-player-pump-trace-evidence-nov05.py',
                 'ced5a453060aae7fb1bb5d84743f93697f744251de9f4c3b306b3234bb9a044f',
                 mux_source, dict(pump_verify=pump))
    proof = mux(native)
    proof.update(slotObserverBinding=True, hardwareProfileUnchangedFromOriginalA=True,
                 oldHistoricalAVmGeometryRecovered=False, completeGame=False)
    for path in [H / 'observer-slots-v2/prepared.json', Path(__file__).resolve()]:
        data = path.read_bytes()
        proof['bindings'][path.relative_to(R).as_posix()] = dict(bytes=len(data), sha256=SHA(data))
    return proof


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    native, output = args.native.resolve(), args.output.resolve()
    assert native.is_relative_to(H) and output.is_relative_to(H) and not output.exists()
    value = verify(native)
    output.write_text(json.dumps(value, indent=2)+'\n')
    print(json.dumps({key: value[key] for key in ['verifiedFiniteOriginalRegisterReadEvidence',
        'accessEvents', 'arithmeticPairsEqual', 'actualMuxBoundaryEvents',
        'actualPostPlayerPumpBeforeFirstReadObserved', 'ordinaryIndependentTimingAccepted']}))
