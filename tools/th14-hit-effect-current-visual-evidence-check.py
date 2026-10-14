"""Retain complete TH14 raw32 comparisons and separately diagnose visual increments.

Absolute visual state remains part of the comparison. Increment analysis does
not subtract a seed/count baseline from the equality result, mask fields, trim
loading callbacks, or change either executable's state.
"""
import array
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RT = ROOT / "runtimes/th12/th12_web"
CURRENT = ROOT / "artifacts/th14/public-replay-playback/zps-reimua-lunatic-hit-effects-oct14"
BEFORE = ROOT / "artifacts/th14/public-replay-playback/zps-reimua-lunatic-focused-growth-oct14"
TRACE = ROOT / "artifacts/th14/native-zps-reimua-lunatic-full-oct14/reference.compact.json"
RECEIPT = TRACE.with_name("reference.compact.compact-receipt.json")
OUTPUT = ROOT / "docs/porting/th14-hit-effect-current-visual-verified-oct14.json"
FIELDS = ["stageFrame", "held", "pressed", "x", "y", "lifeState", "stateAge", "transitionAge",
          "shootingAge", "invincibility", "shotAge", "focused", "score", "graze", "pointValue", "power",
          "lives", "lifePieces", "bombs", "bombPieces", "rank", "visualSeed", "visualCalls",
          "gameplaySeed", "gameplayCalls", "enemyCount", "shots", "character", "subtype", "difficulty",
          "stage", "scaleFlags"]
SHA = lambda data: hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as file:
        while data := file.read(4 * 1024 * 1024):
            h.update(data)
    return h.hexdigest()


def bind(path):
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size, "sha256": digest(path)}


def verify_playback(directory, current=False):
    report = read(directory / "report.json")
    assert report["physicalInvocationOrder"] and report["transitionCallbacksRetained"]
    assert not report["invulnerabilityOverride"] and not report["forcedProgression"]
    raw = (directory / "selected-state.u32").read_bytes()
    active = (directory / "callback-active.u8").read_bytes()
    assert SHA(raw) == report["selectedStateSha256"]
    assert SHA(active) == report["callbackActiveSha256"]
    assert len(raw) == report["selectedSamples"] * 32 * 4
    assert len(active) == report["selectedSamples"]
    assert len([value for value in active if not value]) == report["inactiveCallbacksRetained"]
    assert digest(directory / "public-replay.wasm") == report["wasmSha256"]
    if current:
        for path, expected in report["sourceHashes"].items():
            assert digest(RT / path) == expected, path
        for file, key in (("th14-public-replay-physical-fixture.cpp", "fixtureSha256"),
                          ("th14-custom-replay-reference-fixture.cpp", "includedFixtureSha256"),
                          ("th14-session-reference-fixture.cpp", "sessionFixtureSha256")):
            assert digest(RT / "tests/cpp" / file) == report[key], file
        assert digest(ROOT / "tools/th14-public-replay-physical-playback-check.mjs") == report["toolSha256"]
        replay_path = ROOT / "artifacts/th14/public-replay-reference/th14_udzp01.rpy"
        metadata = read(replay_path.with_name("th14_udzp01-source.json"))
        assert digest(replay_path) == report["replaySha256"] == metadata["sha256"]
        assert report["replaySource"] == metadata
        target = read(ROOT / "runtimes/th14/target.json")
        archive = target["dataArchives"]["th14.dat"]
        assert digest(Path(archive["path"])) == "57d84a5cbe82460931cca26f090a0fde7aef180889ce5bfe8315851fc97b0233"
    words = array.array("I")
    words.frombytes(raw)
    return report, words, active


def normalized(row):
    g, player = row["globals"], row["player"]
    values = [row["stageFrame"], row["held"], row["pressed"], *player[:9],
              g[2], g[6], g[9], g[12], g[15], g[16], g[18], g[19], g[5],
              row["scriptRng"][0], row["scriptRng"][2], row["replayRng"][0], row["replayRng"][2],
              row["enemyCount"], row["shots"], *row["selection"], row["scaleFlags"]]
    assert len(values) == 32
    return [v & 0xffffffff for v in values]


def compare(frames, words, active):
    count = min(len(frames), len(words) // 32)
    differences, increment_differences = [], []
    counts, stage_counts = Counter(), Counter()
    first = {}
    for index in range(count):
        row = frames[index]
        assert row["index"] == index
        expected = normalized(row)
        observed = words[index * 32:(index + 1) * 32]
        stage_counts[row["selection"][3]] += 1
        for field, (actual, target) in enumerate(zip(observed, expected)):
            if actual == target:
                continue
            item = {"index": index, "stage": row["selection"][3], "stageFrame": row["stageFrame"],
                    "active": bool(active[index]), "field": FIELDS[field], "port": actual, "native": target}
            counts[FIELDS[field]] += 1
            differences.append(item)
            first.setdefault(FIELDS[field], item)
        if index:
            port_inc = int(words[index * 32 + 22]) - int(words[(index - 1) * 32 + 22])
            native_inc = row["scriptRng"][2] - frames[index - 1]["scriptRng"][2]
            if port_inc != native_inc:
                increment_differences.append({"index": index, "stage": row["selection"][3],
                                             "stageFrame": row["stageFrame"], "active": bool(active[index]),
                                             "port": port_inc, "native": native_inc,
                                             "difference": port_inc - native_inc})
    return count, differences, dict(counts), first, dict(stage_counts), increment_differences


def write_private(name, data):
    path = CURRENT / name
    path.write_text(json.dumps(data, separators=(",", ":")) + "\n", encoding="utf-8")
    return bind(path)


def main():
    receipt = read(RECEIPT)
    assert receipt["allValuesEqual"] and receipt["frames"] == 90793
    assert digest(ROOT / "tools/th14-native-trace-compact.py") == receipt["toolSha256"]
    assert digest(TRACE) == receipt["outputSha256"]
    original = ROOT / receipt["source"]
    assert original.stat().st_size == receipt["sourceBytes"] and digest(original) == receipt["sourceSha256"]
    trace = read(TRACE)
    frames = trace["frames"]
    assert len(frames) == trace["capturedFrames"] == 90793
    assert trace["error"] == "" and not trace["timedOut"] and trace["noInputInjection"]
    assert trace["executableSha256"] == digest(Path("H:/Games/th/14/th14.exe"))
    assert digest(ROOT / "tools/th14-native-stored-bootstrap-capture.py") == trace["warmReplayCaptureToolSha256"]
    assert digest(ROOT / "tools/th14-native-first-loader-angle-capture.py") == trace["lateCollisionObserver"]["toolSha256"]
    init = trace["caseInitialization"]
    assert trace["childGameStateOverrides"] == 1
    assert (init["address"], init["before"], init["after"], init["wordWrites"]) == ("0x4f58b8", 0x40, 0, 1)
    assert init["afterReadOnlyBootstrap"] and init["beforeFirstPlayerInstruction"]
    report, words, active = verify_playback(CURRENT, current=True)
    before, before_words, before_active = verify_playback(BEFORE)
    engine_path = ROOT / "runtimes/th13/th13_web/artifacts/cpp/engine-th14-build.json"
    engine = read(engine_path)
    assert engine["sourceHashes"] == report["sourceHashes"]
    assert len(report["sourceHashes"]) == 265
    resource_evidence_path = ROOT / "docs/porting/th14-hit-effect-resource-verified-oct14.json"
    evidence = read(resource_evidence_path)
    assert evidence["passed"] and evidence["firstRuntimeIncrementDifference"] == 358
    assert digest(ROOT / "tools/th14-hit-effect-resource-evidence-check.py") == evidence["toolSha256"]
    count, differences, counts, first, stages, increments = compare(frames, words, active)
    before_count, _, before_counts, _, _, before_increments = compare(frames, before_words, before_active)
    assert before_count == 90793
    assert before_counts["visualCalls"] == 90793 and before_counts["visualSeed"] == 90777
    assert len(before_increments) == 18712 and before_increments[0]["index"] == 358
    selected = []
    for index in (358, 364, 366, 372):
        assert index < count
        row = frames[index]
        selected.append({"index": index, "stageFrame": row["stageFrame"],
                         "native": row["scriptRng"][2] - frames[index - 1]["scriptRng"][2],
                         "before": int(before_words[index * 32 + 22]) - int(before_words[(index - 1) * 32 + 22]),
                         "current": int(words[index * 32 + 22]) - int(words[(index - 1) * 32 + 22])})
    active_increments = [item for item in increments if item["active"]]
    gameplay = [item for item in differences if item["field"] not in ("visualSeed", "visualCalls")]
    bindings = [bind(path) for path in (TRACE, original, RECEIPT, engine_path, resource_evidence_path,
        ROOT / "tools/th14-hit-effect-resource-evidence-check.py",
        ROOT / "tools/th14-public-replay-physical-playback-check.mjs",
        ROOT / "tools/th14-native-trace-compact.py",
        ROOT / "tools/th14-native-first-loader-angle-capture.py",
        ROOT / "tools/th14-native-stored-bootstrap-capture.py",
        ROOT / "artifacts/th14/public-replay-reference/th14_udzp01-source.json",
        ROOT / "runtimes/th14/target.json")]
    for directory in (CURRENT, BEFORE):
        bindings.extend(bind(directory / name) for name in
                        ("report.json", "selected-state.u32", "callback-active.u8", "public-replay.wasm"))
    result = {
        "diagnosticEvidenceVerified": True, "passed": count == len(frames) and not differences,
        "completeGame": False, "nativeEquivalent": False, "physicalInvocationOrder": True,
        "loadingCallbacksIncluded": True, "sourceFilesVerified": len(report["sourceHashes"]),
        "comparedCallbacks": count, "nativeCapturedCallbacks": len(frames), "candidateCapturedCallbacks": len(words) // 32,
        "remainingNativeCallbacks": len(frames) - count, "rawWords": count * 32, "stages": stages,
        "absoluteRaw32Differences": len(differences), "fieldDifferenceCounts": counts, "firstDifferences": first,
        "gameplayDifferences": len(gameplay), "firstRemainingGameplayDifferences": gameplay[:8],
        "allRemainingGameplayDifferencesDuringInactiveLoading": all(not item["active"] for item in gameplay),
        "equalSelectedGameplayFields": [field for field in FIELDS if field not in ("visualSeed", "visualCalls") and not counts.get(field)],
        "allAbsoluteDifferences": write_private("hit-effects-raw32-differences.json", differences),
        "visualIncrementDiagnostic": {
            "doesNotModifyAbsoluteEquality": True, "comparisons": max(0, count - 1),
            "beforeDifferences": len(before_increments), "currentDifferences": len(increments),
            "currentActiveDifferences": len(active_increments), "currentInactiveDifferences": len(increments) - len(active_increments),
            "firstRemainingDifference": increments[0] if increments else None,
            "firstRemainingActiveDifference": active_increments[0] if active_increments else None,
            "beforeFirstFocusedHitOffsets": selected,
            "allCurrentIncrementDifferences": write_private("hit-effects-visual-increment-differences.json", increments)},
        "startupAbsoluteDifference": {
            "current": {"seed": words[21], "calls": words[22]},
            "native": {"seed": frames[0]["scriptRng"][0], "calls": frames[0]["scriptRng"][2]},
            "differentExternalClockAndLoadingDurationRetained": True},
        "candidatePlaybackEnded": report["candidatePlaybackEnded"], "nativeCaseInitialization": init,
        "bindings": bindings, "toolSha256": digest(Path(__file__)),
        "scope": "Every current intact ReimuA Lunatic callback is compared in physical order with the full original90793 trace, including inactive loading and repeated/reset clocks. All32 absolute fields and every mismatch are retained; no masking, callback deletion, resynchronization, seed/counter correction or forced completion. A separate diagnostic subtracts successive visual call counters within each unchanged stream to locate remaining consumption differences; it does not make differing absolute visual state pass. Before focused-growth raw evidence remains immutable. One declared initial warm Replay flag clear remains. Full object-owner memory, ordinary startup/ending, pixels/audio/storage and whole-game1:1 are not certified."
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"diagnosticEvidenceVerified": True, "passed": result["passed"], "callbacks": count,
                      "absoluteDifferenceCounts": counts, "beforeIncrementDifferences": len(before_increments),
                      "currentIncrementDifferences": len(increments), "firstRemainingActive": result["visualIncrementDiagnostic"]["firstRemainingActiveDifference"]}))


if __name__ == "__main__":
    main()
