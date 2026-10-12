"""Record the 2026-10-09 HUD/Bomb increment and its observed browser captures.
This records existing evidence; it does not turn diagnostics into equivalence proofs.
"""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RT=ROOT/'runtimes/th12/th12_web'
SDL='f50ab9bffe9c536188a442fb9dd06f6087016a81986a70501e2f56ccff5f6941'
HUD_BUILD='893c8731be74843a805100835bf99148a33b93b28e414b09191b123c6989d4dd'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def write(p,data):(ROOT/p).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def ref(p):return dict(report=p,sha256=sha(p))
def main():
    build=read('runtimes/th14/th14_web/artifacts/sdl3/build.json')
    assert build['sha256']==SDL and sha('runtimes/th14/th14_web/artifacts/sdl3/th11-harness.wasm')==SDL
    browser_path='docs/porting/browser-th14-hud-icons-oct09.json'
    captures=[]
    for name,frame,lives,bombs,note in (
        ('start',186,2,3,'Normal/Reimu A: initial stocks and completed icon fade.'),
        ('bomb',277,2,3,'Reimu A attempt refused script 35; unchanged stock is a failure observation.'),
        ('death',998,0,3,'Natural deaths reduce full life icons.'),
        ('loss',1293,0,3,'Natural game over; before the first Continue.'),
        ('continue',1462,2,3,'First Continue preserves the battle; respawn restores three Bombs.')):
        p=f'artifacts/th14/browser-hud-icons-{name}-oct09.jpg'
        captures.append(dict(screenshot=p,sha256=sha(p),buildSha256=HUD_BUILD,stage=1,frame=frame,fullLifeIcons=lives,fullBombIcons=bombs,note=note))
    for name,frame,note in (
        ('marisa',513,'Frontend pause after the live Marisa A Bomb: two full Bomb icons, no collector abort.'),
        ('marisa-clean',905,'Unobstructed live view: one full life icon, two full Bomb icons, one Bomb fragment. The inherited Bomb animation/cancellation is still incorrect.')):
        p=f'artifacts/th14/browser-bomb-damage-{name}-oct09.jpg'
        captures.append(dict(screenshot=p,sha256=sha(p),buildSha256=SDL,stage=1,frame=frame,fullLifeIcons=1,fullBombIcons=2,note=note))
    write(browser_path,dict(date='2026-10-09',verified=False,url='http://127.0.0.1:8126/',servedBuild=dict(bytes=build['bytes'],sha256=SDL),
        servedAssetCheck='Read-only HTTP GET /th11-harness.wasm returned 1,711,445 bytes with the same SHA-256 after the browser reload.',
        captures=captures,consoleErrors=[],scope='Observed browser rendering and real input only. Historical HUD captures use the earlier HUD-only build; current Marisa captures use the damage fix. No native replay, physical audio or GPU pixel-equivalence assertion. Five Bomb startups still fail and Marisa A effects remain inherited.'))
    index_path='docs/porting/th14-end-ascii-manual-progress-oct09.json';index=read(index_path)
    for name in ('th14-hud-icons','th14-bomb-damage'):
        index['proofs'][name]=dict(report=f'docs/porting/{name}-verified.json')
    for name,entry in index['proofs'].items():
        report=read(entry['report']);assert report['passed']
        for p,h in report.get('sourceHashes',{}).items():assert hashlib.sha256((RT/p).read_bytes()).hexdigest()==h,(name,p)
        entry.update(sha256=sha(entry['report']),passed=True,scope=report['scope'])
    index['scope']='TH14 bounded proofs: ETEX, end menus, ASCII/manual, Continue/HUD, player lifecycle, respawn filtering, decoder restoration, sixteen managed stock icons and active-Bomb damage collection. All-title, native replay, full Bomb effects, physical audio and GPU pixel equivalence remain unverified.'
    index['implemented'] += [s for s in (
        'Sixteen retail front.anm life/Bomb icons registered with AnmManager; layer 24, native fade/stock interrupts, once-per-frame updates and cleanup. Legacy TH11 communication/extra-icon bindings are excluded for TH14.',
        'TH14 six direct Bomb damage virtuals return zero; an active Bomb now preserves normal/death damage-area collection instead of aborting the battle.') if s not in index['implemented']]
    index['sdl']=dict(wasm='runtimes/th14/th14_web/artifacts/sdl3/th11-harness.wasm',bytes=build['bytes'],sha256=SDL,buildLog='artifacts/th14/bomb-damage-sdl-build.log')
    for row in index['sharedEngineBuilds']:
        b=read(row['report']);row.update(bytes=b['bytes'],sha256=b['sha256'],sources=b['engineSources'])
    index['historicalPlayerLifecycleBrowserReport']=index.get('historicalPlayerLifecycleBrowserReport',index['browserReport'])
    index['browserReport']=browser_path;index['browserReportSha256']=sha(browser_path)
    remaining=[
        'Six complete TH14 Bomb effect paths remain unreconstructed: Reimu A/B, Marisa B and Sakuya A/B still refuse legacy scripts 35/33/43/47/58. Marisa A no longer aborts damage collection but its startup/animation/areas/cancellation are inherited and incorrect.',
        'Sakuya B requires actual 110-frame bullet/laser time stop, frozen collision dispatch, radius-600 type-3 cancellation and double item delivery. Native startup evidence is not port verification.',
        'Result/spell/timer HUD layouts, complete alpha integration and remaining sprite/pixel differences; sixteen sidebar stock icons now have bounded interpreter/registration/render proofs.',
        'Complete player movement/options/invulnerability/area integration and native replay lifecycle; physical queued audio and native DirectSound PCM equality remain unverified.',
        'Retail score/ranking container and replay saving; complete pause/result menus, D3DX PNG resampling/color quantization and full GPU comparison.',
        'Other ETEX, manager bounds, kind-0 laser fragments and ordinary complete-game verification.',
        'Other requested unported titles TH06nc/TH12/TH13/TH16/TH17/TH18/TH19 remain unfinished. Completed titles are excluded from port scope.'
    ]
    index['remaining']=remaining
    refs_path=index['references'];refs=read(refs_path)
    for row in refs['references']:
        if row['url']=='https://github.com/YomotsuHisami/th11':
            addition=' HUD icon registration must follow TH14 manager-owned layer 24 rather than embedded TH11 VMs. Actual Bomb animation scripts and damage virtuals also differ; the shared TH11 Bomb controller remains a known incomplete path.'
            if addition not in row['application']:row['application']+=addition
    if not any(r['url']=='https://github.com/thpatch/thtk' for r in refs['references']):
        files=['reference/thtk/README','reference/thtk/thanm/thanm.c']
        refs['references'].append(dict(url='https://github.com/thpatch/thtk',commit='892114a0fcaa0bbdaaecf3cb4ad56f758683fb40',files=files,
            application='Reviewed the TH14 archive/ANM tooling and supported-title table while tracing retail front.anm scripts and Bomb resource script differences.',
            limit='Resource formats and script inspection provide leads; neither the tool support table nor a decoded ANM establishes runtime, Bomb or pixel equivalence.',fileSha256={p:sha(p) for p in files}))
    write(refs_path,refs);index['referencesSha256']=sha(refs_path)
    write(index_path,index)
    proof_names=['th14-hud-icons','th14-hud-notice','th14-hud-text','th14-bomb-damage','th14-player-lifecycle','th14-end-session']
    progress=dict(date='2026-10-09',verified=False,scope=index['scope'],proofs={n:index['proofs'][n] for n in proof_names},sdl=index['sdl'],
        sharedEngineBuilds=index['sharedEngineBuilds'],browser=ref(browser_path),references=ref(refs_path),
        regressions=dict(th12Tests=4,th12Log='artifacts/th14/bomb-damage-th12-session-regression.log',lifecycleCases=796,sessionFrames=2197),
        bombDiagnostics=dict(before=ref('artifacts/th14/bomb-activation-before-damage-fix.json'),after=ref('artifacts/th14/bomb-activation-repro.json'),
            nativeStartup=ref('artifacts/th14/bomb-start-native.json'),nativeStartupCases=72,nativeStartupPortVerified=False,
            nativeDamage=ref('artifacts/th14/bomb-damage-native.json'),marisaAFollowupFrames=360,completeBombVerified=False),remaining=remaining)
    write('docs/porting/th14-hud-icons-progress-oct09.json',progress)
    core=ROOT/'docs/porting/CORE_STATUS.md';text=core.read_text(encoding='utf8')
    heading='## 2026-10-09 追加：TH14 库存图标与 Bomb 伤害中断'
    section=f'''{heading}

生命／Bomb 图标此前绑定在旧作嵌入式 VM 中，TH14 没有对应 HudOuter 调度，导致图标缺失。现按原版 42edf6 将 scripts 29..44 的 16 个 VM 注册到 AnmManager，由原脚本选择 layer 24；管理器每帧更新一次并绘制，Hud 析构注销。TH14 不再创建旧作通信 scripts 32..35 和额外 script 44。数字透明度读取第一颗实际生命图标。

实际 front.anm 的原版完整 ANM 解释器比较 **5,792 帧**，覆盖时钟、淡入、颜色、位置、库存／碎片中断。生产绘制 16 图标、96 顶点并验证注销；图像像素仍未比较。HUD 通知 392＋16＋54 组、数字 576 组／25,920 字形、自然失误与三次续关 2,197 帧回归通过。浏览器实测死亡后满心减少、续关补回两颗心／三颗星，记录见 [图标浏览器记录](browser-th14-hud-icons-oct09.json)。

六机体实际 Bomb 启动诊断发现 TH11 控制器尚未移植，原始失败记录保留。另修复伤害收集器误将所有激活 Bomb 判为错误：TH14 六个 vtable +0xc 原版函数均返回 0，真正 Bomb 伤害经玩家区域池处理。**54 次原版直接调用、48 组原版／生产收集比较**通过；魔理沙 A 激活后额外运行 360 帧不再触发 shots=13 中断，浏览器星星由三颗减少到两颗。但其效果仍是旧作逻辑，另外五机体仍拒绝错误脚本，不能认定 Bomb 完成。已实际提取六条启动虚函数的 72 组原版观察（`portVerified: false`）。咲夜 B 的 110 帧时间停止、冻结碰撞、半径 600 的类型 3 消弹及双道具掉落仍待接通。

最新 SDL WASM **1,711,445 字节**，SHA-256 `{SDL}`；本机 HTTP 实际返回资产哈希相同。TH12／TH13 共享 117 源码构建通过、TH12 4 项启动／会话／渲染回归通过、796 组生命周期回归通过。参考继续核对 TH11 eagler、thtk、MERLIN 的版本边界，不把旧作行为直接当作 TH14 证明。总证据索引现为 17 项，进度见 [本轮记录](th14-hud-icons-progress-oct09.json)，整体仍为 `verified: false`。

'''
    if heading not in text:core.write_text(text.replace('## 验收与剩余工作',section+'## 验收与剩余工作',1),encoding='utf8')
    print(f'Recorded {len(captures)} browser captures, {len(index["proofs"])} source-current bounded proofs, and incomplete six-Bomb diagnostics.')
if __name__=='__main__':main()
