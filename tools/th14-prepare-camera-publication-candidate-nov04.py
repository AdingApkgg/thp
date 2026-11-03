"""Freeze a TH14 draw-publication scheduling candidate without editing the worktree."""
from pathlib import Path
import argparse, hashlib, json

R = Path(__file__).resolve().parents[1]
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(R / 'artifacts/th14') and not out.exists()
    base_path = R / 'artifacts/th14/replay-cadence-reset-nov04/production-core/observer-build.json'
    base = json.loads(base_path.read_bytes())
    assert base['wasmSha256'] == '88c98a25a2eb23b367f1a7a63b33057011f30c4d42902f66438ad170b82f1e5a'
    parent = Path(base['sourceSnapshotRoot'])
    source = out / 'source'
    for name, digest in {**base['sourceHashes'], **base['headerHashes']}.items():
        raw = (parent / name).read_bytes()
        assert sha(raw) == digest, name
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    changes = []

    def edit(name, replacements):
        path = source / 'th12_web/cpp/game' / name
        raw = path.read_bytes()
        text = raw.decode().replace('\r\n', '\n')
        for old, new in replacements:
            assert text.count(old) == 1, (name, old, text.count(old))
            text = text.replace(old, new)
        ending = '\r\n' if raw.count(b'\r\n') == raw.count(b'\n') and b'\r\n' in raw else '\n'
        path.write_bytes(text.replace('\n', ending).encode())
        changes.append(dict(path='th12_web/cpp/game/' + name, beforeSha256=sha(raw), afterSha256=sha(path.read_bytes())))

    parameter = '\n#if PORT_TITLE == 14\n        ,const std::function<bool()>& camera_published\n#endif\n'
    declared = parameter.replace('camera_published\n', 'camera_published={}\n')
    edit('Stage.hpp', [
        ('bool draw_background(AnmRenderer&,SceneCamera&,ScreenFades&);', 'bool draw_background(AnmRenderer&,SceneCamera&,ScreenFades&' + declared + ');'),
        ('bool draw_foreground(AnmRenderer&,SceneCamera&);', 'bool draw_foreground(AnmRenderer&,SceneCamera&' + declared + ');')])
    path = source / 'th12_web/cpp/game/StageDraw.cpp'
    raw = path.read_bytes()
    text = raw.decode().replace('\r\n', '\n')
    for old, new in [
        ('bool Stage::draw_background(AnmRenderer& renderer,SceneCamera& camera,ScreenFades& fades){', 'bool Stage::draw_background(AnmRenderer& renderer,SceneCamera& camera,ScreenFades& fades' + parameter + '){'),
        ('bool Stage::draw_foreground(AnmRenderer& renderer,SceneCamera& camera){', 'bool Stage::draw_foreground(AnmRenderer& renderer,SceneCamera& camera' + parameter + '){')]:
        assert text.count(old) == 1
        text = text.replace(old, new)
    old = 'state.camera.offset=camera.offset;camera=state.camera;renderer.set_camera(camera,false);'
    assert text.count(old) == 2
    text = text.replace(old, '''state.camera.offset=camera.offset;camera=state.camera;
#if PORT_TITLE == 14
        // Retail40e365/40e7f1: the worker can copy the newly published
        // saved camera before446400 replaces its perspective-derived right.
        if(camera_published&&!camera_published()){error="stage camera publication worker failed";return false;}
#endif
        renderer.set_camera(camera,false);''')
    path.write_bytes(text.encode())
    changes.append(dict(path='th12_web/cpp/game/StageDraw.cpp', beforeSha256=sha(raw), afterSha256=sha(path.read_bytes())))
    edit('GameBattle.hpp', [('bool draw(AnmRenderer&,SceneDrawKind);', 'bool draw(AnmRenderer&,SceneDrawKind' + declared + ');')])
    forwarded = '\n#if PORT_TITLE == 14\n            ,camera_published\n#endif\n'
    edit('GameBattle.cpp', [
        ('bool GameBattle::draw(AnmRenderer& renderer,SceneDrawKind kind) {', 'bool GameBattle::draw(AnmRenderer& renderer,SceneDrawKind kind' + parameter + ') {'),
        ('outgoing_stage->draw_background(renderer,compositor.world_camera,fades)', 'outgoing_stage->draw_background(renderer,compositor.world_camera,fades' + forwarded + ')'),
        ('stage->draw_background(renderer,compositor.world_camera,fades)', 'stage->draw_background(renderer,compositor.world_camera,fades' + forwarded + ')'),
        ('outgoing_stage->draw_foreground(renderer,compositor.world_camera)', 'outgoing_stage->draw_foreground(renderer,compositor.world_camera' + forwarded + ')'),
        ('stage->draw_foreground(renderer,compositor.world_camera)', 'stage->draw_foreground(renderer,compositor.world_camera' + forwarded + ')')])
    edit('GameSession.cpp', [
        ('    u32 next_fade_priority=0;\n    for(const auto& pass:scene_draw_passes)', '''#if PORT_TITLE == 14
    const std::function<bool()> camera_published=[this](){
        return !battle||!battle->pending_stage||battle->pump_stage_loading(stage_load_clock(),
            animations.first_deferred_capture_file_index(),stage_load_host_flags);
    };
#endif
    u32 next_fade_priority=0;
    for(const auto& pass:scene_draw_passes)'''),
        ('battle->draw(renderer,pass.kind)', 'battle->draw(renderer,pass.kind' + forwarded + ')')])
    prepared = dict(baseBuild=base_path.relative_to(R).as_posix(), baseBuildSha256=sha(base_path.read_bytes()),
                    sourceRoot=source.as_posix(), changes=changes, rootGameplaySourcesModified=False,
                    onlyTh14BehaviorChanged=True, originalCameraValuesProvidedToEngine=False,
                    arbitraryClockDeliverySelected=False, copyWordInterleavingsImplemented=False,
                    productionIntegrated=False, oldCameraOrRngFailuresClosed=False,
                    completeGame=False, nativeEquivalent=False, preparerSha256=sha(Path(__file__).read_bytes()))
    (out / 'prepared.json').write_bytes((json.dumps(prepared, indent=2) + '\n').encode())
    print(json.dumps(prepared))


if __name__ == '__main__':
    main()
