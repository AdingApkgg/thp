"""Update owned current sections; retain each earlier checkpoint as history."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/th14/staged-loader-current-docs-oct14'
START = '<!-- th14-staged-loader-current:start -->'
END = '<!-- th14-staged-loader-current:end -->'
SHA = lambda data: hashlib.sha256(data).hexdigest()
CHECKPOINT = 'docs/porting/th14-staged-loader-current-checkpoint-oct14.json'
SDL_SHA = '64b46da7c4aa1af2426d024c176e8c77b9ecae5a3da13a1eeea6c648ee82ca54'
HELPER_SHA = 'ef546985ec5786f78a869575cc1e70a41463cd8061ca645139cfe9c3bf1ffebd'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--require-checkpoint', action='store_true')
    args = parser.parse_args()
    bindings = {}

    def load(name):
        path = ROOT / name
        data = path.read_bytes()
        bindings[name] = dict(bytes=len(data), sha256=SHA(data))
        return json.loads(data)

    raw = load('docs/porting/th14-staged-loader-production-raw-evidence-verified-oct14.json')
    assert raw['productionRawEvidenceVerified'] and raw['sourceFilesVerified'] == 267 and raw['engineObjectsVerified'] == 141
    assert not raw['completeGame'] and not raw['nativeEquivalent']
    assert [(row['physicalCallbacks'], row.get('rawGameplayDifferences'), row.get('rawVisualDifferences')) for row in raw['cases']] == [
        (90793, 10, 181570), (98074, None, None), (39458, 0, 78916), (96016, 10, 192016)]
    objects = raw['productionObjects']
    assert (objects['retainedDetailDifferences'], objects['inactiveLoadingDetailDifferences'], objects['activeBattleDetailDifferences']) == (65, 57, 8)
    assert objects['activeAreaDifferenceColumns'] == [8]
    sanitizer = load('artifacts/th14/staged-loader-production-sanitized/staged-loader-oct14/report.json')
    assert sanitizer['sanitizerMatrixVerified'] and sanitizer['sourceHashes'] == raw['sourceHashes']
    assert [row['frames'] for row in sanitizer['cases']] == [90793, 98074, 39458, 96016]
    assert all(row['sanitizerPassed'] and row['allRaw32WordsEqual'] and not row['errors'] for row in sanitizer['cases'])
    storage = load('docs/porting/th14-natural-storage-normal-sakuyaa-staged-loader-oct14-observed-oct14.json')
    assert storage['diagnosticEvidenceVerified'] and storage['passed'] and storage['native']['passed']
    assert (storage['naturalInputFrames'], storage['endingFrames'], storage['scoreBytes'], storage['rawBytes']) == (95220, 3737, 22379, 149076)
    assert storage['finalPhase'] == 0 and storage['titleScreen'] == 1
    candidate = load('docs/porting/th14-deferred-capture-success-dirty-verified-oct14.json')
    assert candidate['privateSuccessDirtyCandidateVerified'] and candidate['candidateHelperSha256'] == HELPER_SHA
    assert (candidate['cases'], candidate['comparedRawBytes'], candidate['exactNativeFullBuffers'], candidate['differentBytes']) == (8, 5242880, 8, 0)
    review = load('artifacts/th14/deferred-capture-independent-review-oct14/candidate-complete-review.json')
    assert review['independentSourceReviewPassed'] and review['candidatePhysicalReviewPassed']
    current_helper = ROOT / 'runtimes/th12/th12_web/cpp/sdl/ApplicationCaptureTh14.hpp'
    assert SHA(current_helper.read_bytes()) == HELPER_SHA
    sdl = load('runtimes/th14/th14_web/artifacts/sdl3-release/build.json')
    assert (sdl['sha256'], sdl['bytes'], len(sdl['sources']), len(sdl['headers'])) == (SDL_SHA, 1890810, 146, 149)
    assert sdl['headers']['th12_web/cpp/sdl/ApplicationCaptureTh14.hpp'] == HELPER_SHA
    assert SHA((ROOT / 'runtimes/th14/th14_web/artifacts/sdl3-release/th11.wasm').read_bytes()) == SDL_SHA
    checkpoint_exists = (ROOT / CHECKPOINT).exists()
    if args.require_checkpoint:
        assert checkpoint_exists, 'Wait for the actual new summary receipt'
    if checkpoint_exists:
        checkpoint = load(CHECKPOINT)
        assert not checkpoint['completeGame'] and not checkpoint['nativeEquivalent']
    OUT.mkdir(parents=True, exist_ok=True)
    paths = ['README.md', 'docs/GITHUB_RELEASE.md', 'docs/porting/CORE_STATUS.md',
             'docs/porting/TH14_METHOD.md', 'docs/porting/TH14_STAGED_LOADER_MINIMUM_IMPLEMENTATION.md']
    changed = []
    for name in paths:
        path = ROOT / name
        prefix = 'docs/porting/' if name == 'README.md' else 'porting/' if name == 'docs/GITHUB_RELEASE.md' else ''
        def link(label, filename):
            return f'[{label}]({prefix}{filename})'
        checkpoint_link = link('本轮汇总检查点', 'th14-staged-loader-current-checkpoint-oct14.json')
        if not checkpoint_exists:
            checkpoint_link += '（收据正在汇总；当前数字以已完成的原始证据为准）'
        body = f'''## TH14 当前阶段 · 实际加载与四槽捕获（2026-10-14）

当前只推进 TH14，整作 1:1 未完成。加载生命周期已合入生产：267 个游戏核心文件、141 个 WASI 对象重新绑定并实跑，未继承私有 v2/v3 的整局通过结果。{checkpoint_link}。

普通换关使用真实单调时间的 60ms 最小等待，按 HUD、Scene、新 Enemy owner、ECL 的顺序完成真实资源工作；SDL 队列执行实际上传。原 HUD result 的 120 与随后 transition 的 30 保留，60ms 等待与 HUD 更新重叠，不能再串行叠加一轮 120。内置四槽 capture 队列直接提供首槽状态，0 也表示 busy；DeferredEnd 在 postDraw 消费。完整 session 重置和直接换关替换先取消延迟 capture，普通 ANM clear 仍保留队列。复制成功才更新目标纹理 revision，ANM material cache 的 invalidate 继续保留。

| 新生产回放 | 物理回调 | 独立 Native 所选玩法字差 | 视觉 RNG 字差 |
| --- | ---: | ---: | ---: |
| 灵梦 A Lunatic | 90,793 | 10（非活跃加载期） | 181,570 |
| 灵梦 B Lunatic | 98,074 | 尚无对应完整 Native 基线 | 尚无对应完整 Native 基线 |
| 灵梦 A Extra | 39,458 | 0 | 78,916 |
| 咲夜 A Normal | 96,016 | 10（非活跃加载期） | 192,016 |

四份不可变输入均在当前无窗口生产核心结束，并重新通过不恢复错误的 ASAN／UBSan；测试明确注入 60Hz 单调时钟，在成功 draw 后执行无目标 capture 退役，不作为 Native 线程时间或实际 GPU 上传证明。Lunatic 新完整对象采集和另一份生产回放的 raw32 字节完全相同；65 项对象差异仍失败，包括 57 项非活跃加载期 enemyNextId 和 8 项活跃伤害区域 Z 原始字差。三处详细窗口位于四、五、六面，各 71 个活跃回调；其余所选玩法字段相同，但所有视觉字差与完整失败数组保留。Native 的 90,793 次采集预算不等于普通原版结局／完整终止。{link('本轮 raw32 与完整对象复算', 'th14-staged-loader-production-raw-evidence-verified-oct14.json')}。

当前普通按键 Normal 重新执行 95,220 帧进入 e05，经过 3,737 帧结局／staff 和实际成绩、录像保存请求返回 Main。22,379 编码字节／149,076 解码字节与原版成绩 loader／writer 的完整编解码边界相同。此证明覆盖无窗口生产流程及编解码，未覆盖普通原版整局菜单／结局、Native 文件系统或浏览器 IndexedDB 持久化。{link('当前普通流程与成绩边界', 'th14-natural-storage-normal-sakuyaa-staged-loader-oct14-observed-oct14.json')}。

延迟复制的独立浏览器候选实测 8 个完整缓冲，共 5,242,880 字节，与实际 original32 D3D9 HAL／D3DX 输出及修改前 WebGL 输出均零差；另有 null resource、null texture 与明确标注的 false-return adapter 三组退役控制。输入是声明的合成后缓冲，使用真实 text52 的 512×512 RGB565 目标与矩形／格式控制；不是完整游戏帧、全部格式、实际 GL 错误／HRESULT 映射或音频等价证明。当前 helper 与已测候选逐字节一致。{link('独立复制像素及成功 dirty 证据', 'th14-deferred-capture-success-dirty-verified-oct14.json')}。

最终正式 SDL 为 1,890,810 字节，SHA-256 `{SDL_SHA}`，146 源码／149 头文件绑定。本机预览固定 `8208`，HTML 使用独立静音适配；发布包音频逻辑不变。最终 64b46 模块的完整浏览器流程和持久化仍待验证，旧版短录像保存／播放证据保持历史版本，不能继承为本轮通过。{link('本机固定预览说明', 'TH14_WORKSPACE_SERVER.md')}。全部自机／难度、普通原版完整流程、图像／音频、浏览器持久化与剩余加载差异继续验收；`completeGame=false`、`nativeEquivalent=false` 保持。
'''
        if name.endswith('TH14_STAGED_LOADER_MINIMUM_IMPLEMENTATION.md'):
            body += '\n下列状态表、旧差异区间及 API 拆分是本轮合入前的冻结计划。其“当前未实施／未修改核心”措辞按历史上下文保留，不能读作现在的状态；诊断窗口仍不得成为等待常量。\n'
        source_bytes = path.read_bytes()
        text = source_bytes.decode('utf-8')
        newline = '\r\n' if '\r\n' in text else '\n'
        normalized = text.replace('\r\n', '\n')
        snapshot = OUT / 'before' / name
        if not snapshot.exists():
            snapshot.parent.mkdir(parents=True, exist_ok=True)
            snapshot.write_bytes(source_bytes)
        managed = START + '\n' + body.rstrip() + '\n' + END
        if START in normalized:
            assert normalized.count(START) == normalized.count(END) == 1
            begin, end = normalized.index(START), normalized.index(END) + len(END)
            updated = normalized[:begin] + managed + normalized[end:]
        else:
            assert normalized.startswith('# ') and '\n\n' in normalized
            title, remainder = normalized.split('\n\n', 1)
            if name == 'README.md':
                assert remainder.count('## 当前状态\n') == 1
                remainder = remainder.replace('## 当前状态\n', '## 历史状态 · 本轮前的矩阵组合与暂停检查点\n', 1)
                updated = title + '\n\n' + managed + '\n\n' + remainder
            elif name == 'docs/GITHUB_RELEASE.md':
                assert remainder.count('## TH14 已验证进度\n') == 1
                remainder = remainder.replace('## TH14 已验证进度\n', '## TH14 历史检查点（各自绑定原版本）\n', 1)
                updated = title + '\n\n' + managed + '\n\n' + remainder
            else:
                updated = title + '\n\n' + managed + '\n\n## 历史记录 · 本轮前的冻结证据与计划\n\n' + remainder
        # Removing only our managed section and historical heading must recover
        # the previous complete document; older evidence prose is never edited.
        historic = snapshot.read_text(encoding='utf-8').replace('\r\n', '\n')
        recovered = updated.replace(managed + '\n\n', '', 1)
        if name == 'README.md':
            recovered = recovered.replace('## 历史状态 · 本轮前的矩阵组合与暂停检查点\n', '## 当前状态\n', 1)
        elif name == 'docs/GITHUB_RELEASE.md':
            recovered = recovered.replace('## TH14 历史检查点（各自绑定原版本）\n', '## TH14 已验证进度\n', 1)
        else:
            recovered = recovered.replace('## 历史记录 · 本轮前的冻结证据与计划\n\n', '', 1)
        assert recovered == historic, 'Historical body changed: ' + name
        result = updated.replace('\n', newline).encode()
        path.write_bytes(result)
        changed.append(dict(path=name, beforeSha256=SHA(snapshot.read_bytes()), afterSha256=SHA(result), historicalBodyPreserved=True))
    receipt = dict(currentDocsPrepared=True, currentCheckpointExists=checkpoint_exists, completeGame=False, nativeEquivalent=False,
                   currentCoreSourceFiles=267, currentEngineObjects=141, currentSdlSha256=SDL_SHA, currentSdlBytes=1890810,
                   finalSdlBrowserFlowVerified=False, helperSha256=HELPER_SHA, documents=changed, evidenceBindings=bindings,
                   toolSha256=SHA(Path(__file__).read_bytes()), scope='Owned current sections only; complete older bodies remain unchanged under historical headings. Fresh core/ASAN/storage evidence and synthetic8-buffer copy scope are distinct. No old browser replay or Native requested budget is promoted to a current final-module/full-game pass.')
    receipt_path = OUT / ('docs-current-complete.json' if checkpoint_exists else 'docs-awaiting-checkpoint.json')
    assert not receipt_path.exists(), 'Completed docs preparation receipt immutable'
    receipt_path.write_bytes((json.dumps(receipt, indent=2) + '\n').encode())
    print(json.dumps(dict(report=str(receipt_path), sha256=SHA(receipt_path.read_bytes()), checkpointExists=checkpoint_exists, documents=len(changed))))


if __name__ == '__main__':
    main()
