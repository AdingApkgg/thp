"""Verify the frozen private v3 custody; never compile or change game sources."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "artifacts/th14/staged-loader-integration-oct14"
V3 = HOME / "cancel-v3"
SOURCE = V3 / "source/runtimes"
WEB = SOURCE / "th12/th12_web"
bindings = {}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bind(path, expected=None, size=None):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    digest = sha(path)
    if expected is not None:
        assert digest == expected, (str(path), digest, expected)
    length = path.stat().st_size
    if size is not None:
        assert length == size, (str(path), length, size)
    key = path.relative_to(ROOT).as_posix()
    bindings[key] = {"bytes": length, "sha256": digest}
    return digest


def read(path, expected=None):
    bind(path, expected)
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def check_map(mapping, base=ROOT):
    for name, digest in mapping.items():
        bind(base / name, digest)


frozen_sha = "d754a50cc94ea8d962b13e595555dba17a6c3621cfda1dbb6eed8772dc446eed"
frozen = read(V3 / "frozen-source.json", frozen_sha)
assert frozen["frozen"] and frozen["revision"] == "cancel-v3"
assert len(frozen["files"]) == 736
for item in frozen["files"]:
    bind(SOURCE / item["path"], item["sha256"], item["bytes"])
assert {p.relative_to(SOURCE).as_posix() for p in SOURCE.rglob("*") if p.is_file()} == {
    item["path"] for item in frozen["files"]
}, "Frozen source inventory changed"

combined = read(V3 / "combined-source.json")
assert combined["combinedPrivateSourceFrozen"]
assert combined["frozenSourceSha256"] == frozen_sha
assert combined["changedFileCount"] == len(combined["changedFiles"]) == 19
baseline = HOME / "baseline"
for item in combined["changedFiles"]:
    bind(V3 / "source" / item["path"], item["newSha256"], item["newBytes"])
    old = baseline / item["path"]
    if item["baselineSha256"] is None:
        assert not old.exists(), str(old)
    else:
        bind(old, item["baselineSha256"], item["baselineBytes"])
bind(combined["combinedPatch"], combined["combinedPatchSha256"])
bind(V3 / "application-composed.patch", combined["applicationHunkPatchSha256"])

wasi = read(V3 / "private-build.json")
assert wasi["privateBuildCompleted"] and len(wasi["objectHashes"]) == 141
check_map(wasi["privateSourceHashes"], WEB)
check_map(wasi["baselineSourceHashes"], baseline / "runtimes/th12/th12_web")
check_map(wasi["objectHashes"])
bind(WEB / "tests/cpp/th14-staged-loader-integration-fixture.cpp", wasi["fixtureSha256"])
bind(V3 / "staged-loader-integration.wasm", wasi["wasmSha256"], 1441802)
bind(ROOT / "tools/th14-staged-loader-integration-check.mjs", wasi["toolSha256"])

sdl = read(V3 / "sdl-release/build.json")
assert sdl["privateSdlBuildPassed"] and sdl["revision"] == "cancel-v3"
assert sdl["frozenSourceSha256"] == frozen_sha
assert len(sdl["objectHashes"]) == 146
for name in ["sourceHashes", "headers", "objectHashes"]:
    check_map(sdl[name])
bind(V3 / "sdl-release/th14.wasm", sdl["wasmSha256"], sdl["wasmBytes"])
bind(V3 / "sdl-release/th14.mjs", sdl["loaderSha256"])
bind(ROOT / "tools/th14-staged-loader-integration-sdl-build.mjs", sdl["toolSha256"])

cancel = read(V3 / "cancellation-verified.json")
assert cancel["privateCancellationVerified"] and len(cancel["cases"]) == 8
assert cancel["sourceBuildSha256"] == sha(V3 / "private-build.json")
assert cancel["wasmSha256"] == wasi["wasmSha256"]
assert cancel["privateSourceHashes"] == wasi["privateSourceHashes"]
bind(ROOT / "tools/th14-staged-loader-integration-cancel-check.mjs", cancel["toolSha256"])

adapter_path = ROOT / "docs/porting/th14-staged-loader-sdl-adapter-owner-verified-oct14.json"
adapter = read(adapter_path)
assert adapter["privateActualAdapterOwnershipVerified"]
assert adapter["resultWords"] == [0, 69, 0, 2]
assert adapter["frozenSourceSha256"] == frozen_sha and not adapter["gpuExecuted"]
bind(WEB / "cpp/sdl/Application.cpp", adapter["applicationSha256"])
bind(WEB / "cpp/sdl/StageUploadsTh14.hpp", adapter["helperSha256"])
application = (WEB / "cpp/sdl/Application.cpp").read_bytes()
for item in adapter["exactApplicationMethods"] + [adapter["exactTickBlock"]]:
    data = item["source"].encode("utf-8")
    assert data in application and hashlib.sha256(data).hexdigest() == item["sha256"]
bind(V3 / "adapter-owner/fixture.cpp", adapter["fixtureSha256"])
bind(V3 / "adapter-owner/adapter-owner.wasm", adapter["wasmSha256"])
bind(ROOT / "tools/th14-staged-loader-sdl-adapter-owner-check.mjs", adapter["toolSha256"])
# Preserve the original failing observer alongside the corrected declared unit.
for name in ["first-failing-observer-fixture.cpp", "first-failing-observer.wasm"]:
    bind(V3 / "adapter-owner" / name)
for name in ["adapter-owner-oct14", "adapter-owner-v2-oct14", "cases-oct14", "wasi-oct14", "sdl-oct14"]:
    bind(ROOT / f"artifacts/th14/staged-loader-integration-frozen-cancel-v3-{name}.log")

support = {}
for name in [
    "th14-stage-upload-owner-unit-verified-oct14.json",
    "th14-loader-supervisor-flags-verified-oct14.json",
    "th14-deferred-capture-intrinsic-final-verified-oct14.json",
    "th14-deferred-reset-policy-unit-verified-oct14.json",
    "th14-staged-loader-integration-object-verified-oct14.json",
]:
    support[name] = read(ROOT / "docs/porting" / name)
helper = support["th14-stage-upload-owner-unit-verified-oct14.json"]
assert helper["privateHelperUnitVerified"] and helper["checks"] == 240 and helper["failedCases"] == 0
supervisor = support["th14-loader-supervisor-flags-verified-oct14.json"]
assert supervisor["diagnosticEvidenceVerified"] and supervisor["executableSha256"] == "f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353"
reset = support["th14-deferred-reset-policy-unit-verified-oct14.json"]
assert reset["privateResetPolicyVerified"] and reset["originalV3SourceManifestSha256"] == frozen_sha
assert len(reset["cases"]) == 4
objects = support["th14-staged-loader-integration-object-verified-oct14.json"]
assert not objects["passed"] and not objects["nativeEquivalent"]
assert len(objects["differences"]) == 10 and all(x["field"] == "replayCalls" for x in objects["differences"])
assert len(objects["detailDifferences"]) == 65
assert sum(x["kind"] == "enemyNextId" for x in objects["detailDifferences"]) == 57
assert sum(x["kind"] == "damageAreas" for x in objects["detailDifferences"]) == 8
assert len(objects["startupVisualDifferences"]) == 181570
bind(objects["rawDetailPath"], objects["rawDetailSha256"])

# Historical receipts stay bound to their own module, never to the new v3 build.
history = read(HOME / "historical-v1-and-baseline-verified.json")
assert history["historicalPrivateV1Restored"] and history["all141OldObjectHashesRestored"]
bind(HOME / "revision-v1/staged-loader-integration-restored.wasm", history["oldWasmSha256"])
v2_build = read(HOME / "cancel-v2/private-build.json")
bind(HOME / "cancel-v2/staged-loader-integration.wasm", v2_build["wasmSha256"])
historical_replays = []
for label, frames, inactive in [
    ("reimua-lunatic", 90793, 750), ("sakuyaa-normal", 96016, 750),
    ("reimub-lunatic", 98074, 750), ("reimua-extra", 39458, 0),
]:
    folder = HOME / f"cancel-v2/playback/{label}-controlled-cancel-v2"
    replay = read(folder / "report.json")
    assert replay["frames"] == frames and replay["inactiveCallbacks"] == inactive
    assert replay["phase"] == 4 and replay["error"] == "" and replay["candidatePlaybackEnded"]
    assert replay["wasmSha256"] == v2_build["wasmSha256"] != wasi["wasmSha256"]
    assert replay["sourceBuildSha256"] == sha(HOME / "cancel-v2/private-build.json")
    assert not replay["forceProgression"] and not replay["invulnerabilityOverride"]
    bind(folder / "selected-state.u32", replay["selectedStateSha256"])
    bind(folder / "callback-active.u8", replay["callbackActiveSha256"])
    historical_replays.append({"label": label, "revision": "cancel-v2", "frames": frames,
                               "inactiveCallbacks": inactive, "appliesToV3": False})

report = {
    "privateFrozenCombinedEvidenceVerified": True,
    "productionChangedByThisTool": False,
    "productionVerified": False,
    "nativeEquivalent": False,
    "completeGame": False,
    "revision": "cancel-v3",
    "frozenSourceSha256": frozen_sha,
    "frozenFiles": len(frozen["files"]),
    "changedFiles": combined["changedFiles"],
    "privateWasi": {"objects": 141, "moduleBytes": 1441802, "moduleSha256": wasi["wasmSha256"]},
    "privateSdlRelease": {"objects": 146, "moduleBytes": sdl["wasmBytes"], "moduleSha256": sdl["wasmSha256"]},
    "cancellation": {"cases": 8, "originalDat": True, "pendingGpuDependency": "declared unit references"},
    "actualApplicationOwnership": {"methods": 6, "tickBlocks": 1, "checks": 69,
                                   "failures": 0, "normalContinuations": 2,
                                   "deviceDependencies": "recording callbacks", "gpuExecuted": False},
    "preservedAdapterObserverFailure": {"failedChecks": 14,
        "reason": "Initial recorder incorrectly required the different owner's pending queue to be empty during unload; the corrected recorder requires all references belonging to the released owner to be absent. Frozen Application/helper bytes were unchanged.",
        "originalFixtureModuleAndLogRetained": True},
    "helperOwnership": {"cases": 30, "checks": 240, "failures": 0},
    "supervisorFlags": {"unmodifiedOriginalCases": 53, "hostCloseBit": "0x80",
                        "positiveWriter0x100": "unknown"},
    "historicalReplays": historical_replays,
    "historicalObjectComparison": {"revision": "private-controlled-v1", "loadingGameplayCallDifferences": 10,
                                    "enemyNextIdDifferences": 57, "damageAreaDifferences": 8,
                                    "visualRngDifferences": 181570, "appliesToV3": False},
    "excludedProductionChange": "ROOT additionally retires deferred captures before full-session/direct-stage clear_animations; not in these frozen19 files or compiled modules. Independent four-case policy report is retained separately.",
    "remainingScope": [
        "Final ROOT four full replays, sanitizer runs, SDL browser execution and ordinary ending checks belong to the separately rebuilt production source.",
        "No v3 full-replay results are inherited from v1/v2; the historical differences remain explicit.",
        "Current capture target pixel format/512x512 RGB565/POINT2 and failure AddDirtyRect behavior remain separate unresolved pixel work.",
        "Actual GPU cancellation, pixels, Native host scheduling/close delivery and whole-game1:1 are not proved by compilation or recording dependencies.",
    ],
    "bindings": bindings,
    "bindingCount": len(bindings),
    "toolSha256": sha(Path(__file__)),
}
output = ROOT / "docs/porting/th14-staged-loader-combined-private-verified-oct14.json"
output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"privateFrozenCombinedEvidenceVerified": True, "frozenFiles": 736,
                  "changedFiles": 19, "bindings": len(bindings), "report": output.relative_to(ROOT).as_posix(),
                  "reportSha256": sha(output)}, ensure_ascii=False))
