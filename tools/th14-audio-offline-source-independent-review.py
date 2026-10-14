"""Read-only source/compile-plan review. Never compiles or executes audio."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PREP = ROOT / 'artifacts/th14/audio-offline-source-prep-oct14'
OUT = ROOT / 'artifacts/th14/audio-offline-independent-review-oct14/source-review.json'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def binding(path):
    path = Path(path)
    data = path.read_bytes()
    return {'path': path.as_posix(), 'bytes': len(data), 'sha256': sha(data)}


def text(path):
    return Path(path).read_text(encoding='utf-8')


def verify(row):
    assert binding(row['path']) == row, row['path']


def location(path, needle):
    content = text(path)
    index = content.index(needle)
    return {'path': Path(path).as_posix(), 'line': content[:index].count('\n') + 1, 'needle': needle}


def main():
    assert not OUT.exists(), 'Review evidence is immutable'
    prepared = binding(PREP / 'prepared.json')
    assert prepared['sha256'] == 'ed1ab1624a46cb030d17d276fbc1e9e8b795a0ca42595d2ac556771043ec3674'
    plan = json.loads((PREP / 'prepared.json').read_bytes())
    fixture = PREP / 'pcm-fixture.cpp'
    shim = PREP / 'silent-sdl/SDL3/SDL.h'
    audio = ROOT / 'runtimes/th12/th12_web/cpp/sdl/AudioDevice.cpp'
    header = audio.with_suffix('.hpp')
    miniaudio = ROOT / 'runtimes/th12/portable/sdl/third_party/miniaudio.h'
    relevant = [fixture, shim, audio, header, miniaudio]
    bound = {row['path']: row for row in plan['fileBindings']}
    for path in relevant:
        verify(bound[path.as_posix()])
    core = plan['currentEngine']
    assert core['sourceCount'] == len(core['sources']) == 267
    assert core['objectCount'] == len(core['objects']) == 141
    verify(core['report'])
    for row in core['sources'] + core['objects']:
        verify(row)
    args = plan['plannedBuild']['arguments']
    assert args[:2] == ['--target=wasm32-wasip1', '-std=c++17']
    include = [arg for arg in args if arg.startswith('-I')]
    assert include == ['-I' + (PREP / 'silent-sdl').as_posix()]
    assert [arg for arg in args if arg.endswith('.cpp')] == [fixture.as_posix(), audio.as_posix()]
    assert [arg for arg in args if arg.endswith('.o')] == [row['path'] for row in core['objects']]
    assert all('/cpp_game_' in row['path'] for row in core['objects'])
    assert not any(arg.startswith('-l') or 'sdl3' in arg.lower() for arg in args)
    assert plan['plannedBuild']['linkedSdlLibraries'] == []
    assert plan['plannedBuild']['wasiPreopens'] == {}
    assert plan['plannedBuild']['musicPlaybackRequested'] is False
    assert args[-2:] == ['-o', (PREP / 'pcm-offline.wasm').as_posix()]
    ft, st, at, ht, mt = [text(path) for path in relevant]
    assert '#ifndef TH14_OFFLINE_AUDIO_SHIM' in ft
    assert 'TH14_OFFLINE_AUDIO_SHIM == 1 && sizeof(SDL_AudioStream) == 1' in ft
    assert '#include <SDL3/SDL.h>' in ht
    assert at.startswith('#define MA_NO_DEVICE_IO\n')
    assert '#define MA_NO_THREADING' in at and 'engine.noDevice=MA_TRUE' in at
    assert '#if !defined(MA_NO_DEVICE_IO)\n    {\n        pEngine->pDevice = engineConfig.pDevice;' in mt
    assert '#define TH14_OFFLINE_AUDIO_SHIM 1' in st and 'struct SDL_AudioStream {};' in st
    assert 'return &th14_offline_sdl::stream;' in st
    assert 'return true; // A counter only; there is no device or playback operation.' in st
    assert 'return false; // Fail closed if anyone accidentally invokes AudioDevice::pump.' in st
    shim_code = re.sub(r'/\*.*?\*/|//[^\n]*', '', st, flags=re.S)
    assert not re.search(r'\b(?:extern|dlopen|LoadLibrary|AudioContext|CreateThread|fopen|system)\b', shim_code)
    exports = re.findall(r'^API\(([^)]+)\)', ft, re.M)
    assert 'pump' not in exports and '.pump(' not in ft
    assert set(exports) == {'allocate','release','open_archive','audio_reset','stop_all','command','queued_positioned','mix','mixed_frames','sample_data','sample_bytes','sample_metadata','silent_boundary_counter','error'}
    assert 'if (!frames || frames > 4096 || !audio_ready) return nullptr;' in ft
    assert 'audio.mix(pcm.data(), frames)' in ft
    assert 'audio.music(-1)' in ft and not re.search(r'audio\.music\((?!-1\))', ft)
    locations = [location(audio, '#define MA_NO_DEVICE_IO'), location(audio, 'engine.noDevice=MA_TRUE'),
                 location(miniaudio, '#if !defined(MA_NO_DEVICE_IO)\n    {\n        pEngine->pDevice = engineConfig.pDevice;'),
                 location(header, '#include <SDL3/SDL.h>'), location(fixture, '#ifndef TH14_OFFLINE_AUDIO_SHIM'),
                 location(fixture, 'API(mix)'), location(shim, 'SDL_OpenAudioDeviceStream'),
                 location(shim, 'SDL_ResumeAudioStreamDevice'), location(shim, 'SDL_PutAudioStreamData')]
    for path in relevant:
        verify(bound[path.as_posix()])
    assert binding(PREP / 'prepared.json') == prepared
    result = dict(passed=True, blockingIssues=[], sourcePreparationSha256=prepared['sha256'],
                  sourceFilesRehashed=267, objectsRehashed=141, noHardwareUnderBoundCompilePlan=True,
                  privateSdlHeaderForcedForBothTranslationUnits=True, miniaudioDeviceIoDisabled=True,
                  noDeviceEngineConfiguration=True, linkedRealSdlLibraries=[], exportedEntryPoints=exports,
                  pumpExported=False, sdlBoundaryIsLocalCounterOnly=True, putAudioFailsClosed=True,
                  compiledModuleImportsReviewed=False, fixtureExecuted=False, compilersStarted=0,
                  actualAudioDevicesOpened=0, browserContextsCreated=0, nativeProcessesStarted=0,
                  pcmGenerated=False, productionChanged=False, originalInputsRehashedByThisReview=False,
                  sourceLocations=locations, bindings=[prepared, *[bound[path.as_posix()] for path in relevant], core['report']],
                  checker=binding(__file__),
                  scope='Independent static source and compile-plan review only. The pinned plan compiles the unchanged actual AudioDevice.cpp with the private SDL header, no SDL library, explicit141 game objects and WASI target. MA_NO_DEVICE_IO excludes miniaudio device implementation; engine.noDevice is also true. The SDL stub returns an empty local stream and all open/resume/pause/destroy paths only alter counters; PutAudioStreamData fails. The fixture exports bounded in-memory mix and no pump/Application entry. All267 source and141 object hashes were independently rechecked. This establishes the bound source-plan boundary, not that a future compiler used the plan: final module imports, closed host ABI and runtime counters still require separate review. No compiler, module, audio device, browser or Native process is run here. Native DirectSound PCM, physical silence/output and audio1:1 remain unproved.')
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open('x', encoding='utf-8', newline='\n') as output:
        json.dump(result, output, ensure_ascii=False, indent=2)
        output.write('\n')
    print(json.dumps({'passed': True, 'report': OUT.as_posix(), 'sha256': binding(OUT)['sha256'], 'blockingIssues': []}))


if __name__ == '__main__':
    main()
