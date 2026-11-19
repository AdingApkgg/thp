"""Register TH143 in the standard launcher without workstation paths."""
from pathlib import Path
import argparse,hashlib,json,re
p=argparse.ArgumentParser();p.add_argument('site',type=Path);a=p.parse_args();site=a.site
layout='sha256-'+hashlib.sha256(b'th143/content/1:indexed-independent-gzip:2026-11').hexdigest()
product='''    th143: Object.freeze({
        testOnly: true, buildOptIn: true,
        number: "14.3", title: "弾幕アマノジャク", subtitle: "Impossible Spell Card",
        cardArtwork: "th143-card.webp",
        storage: Object.freeze({saveRoot: "/savesth143", scoreFile: "scoreth143.dat", configFiles: Object.freeze(["th143.cfg"])}),
        runtime: "./runtime/th143/th143.html", runtimeFileLayout: "directory",
        runtimeAssets: Object.freeze(["th143.html", "manifest.json", "launcher-adapter.mjs", "interactive-v124.mjs", "play.wasm", "host-keyboard-input-bridge.mjs"]), requiredShared: Object.freeze([]),
        runtimeResourceTransport: "resources", dataProvider: "retail-memory",
        musicCapabilities: Object.freeze({midi: false}), musicRuntime: Object.freeze({localOggConfigureMode: "runtime-selection", embeddedOgg: true}),
        touchFire: TOGGLE_TOUCH_FIRE,
        support: Object.freeze({highRefreshRate: false, sourceRepository: "https://github.com/AdingApkgg/thp", adaptationNotice: "early-test"}),
        package: Object.freeze({dataFileId: "game-data", dataTarget: "/th143.data", musicSourceDirectories: Object.freeze({ogg: "music"}), musicMounts: Object.freeze({ogg: "/music"})}),
        replay: Object.freeze({prefix: "th143"}), features: Object.freeze({thprac: false, languages: false, focusHitbox: false}),
    }),
'''
path=site/'common/contracts/product-catalog.mjs';text=path.read_text(encoding='utf-8')
if '    th143:' in text:text=re.sub(r'    th143: Object.freeze\(\{.*?(?=    th15: Object.freeze)',lambda _:product,text,flags=re.S)
else:text=text.replace('    th15: Object.freeze({',product+'    th15: Object.freeze({',1)
start=text.index('    th14: Object.freeze({');end=text.index('    th143:',start)
if 'multiplayerRuntime:' not in text[start:end]:text=text[:start]+text[start:end].replace('        runtime: "./runtime/th14/th14.html",','        runtime: "./runtime/th14/th14.html",\n        multiplayerRuntime: "./runtime/th14/multiplayer/th14.html",')+text[end:]
path.write_text(text,encoding='utf-8',newline='\n')
declaration='''    th143: Readonly<{
        testOnly: true; buildOptIn: true; number: "14.3"; title: string; subtitle: string; cardArtwork: "th143-card.webp";
        storage: Readonly<{saveRoot: "/savesth143";scoreFile: "scoreth143.dat";configFiles: readonly string[]}>;
        runtime: "./runtime/th143/th143.html";runtimeFileLayout: "directory";runtimeAssets: readonly string[];requiredShared: readonly string[];
        runtimeResourceTransport: "resources";dataProvider: "retail-memory";
        musicCapabilities: Readonly<{midi: false}>;musicRuntime: Readonly<{localOggConfigureMode: "runtime-selection";embeddedOgg: true}>;
        touchFire: Readonly<{mode: "toggle";labelKey: "touch.tapToggle"}>;
        support: Readonly<{highRefreshRate: false;sourceRepository: string;adaptationNotice: "early-test"}>;
        package: Readonly<{dataFileId: "game-data";dataTarget: "/th143.data";musicSourceDirectories: Readonly<{ogg: "music"}>;musicMounts: Readonly<{ogg: "/music"}>}>;
        replay: Readonly<{prefix: "th143"}>;features: Readonly<{thprac: false;languages: false;focusHitbox: false}>;
    }>;
'''
path=site/'common/contracts/product-catalog.d.mts';text=path.read_text(encoding='utf-8')
if '    th143:' not in text:text=text.replace('    th15: Readonly<{',declaration+'    th15: Readonly<{',1)
path.write_text(text,encoding='utf-8',newline='\n')
path=site/'launcher/lib/content-definition.mjs';text=path.read_text(encoding='utf-8')
content='    th143: Object.freeze({original: Object.freeze({files: Object.freeze(["th143.data"])}), dataLayout: '+json.dumps(layout)+', music: Object.freeze({}),hostPreparation: Object.freeze({preparedContent: Object.freeze({directory: "content",markerFiles: Object.freeze(["th143.data"])}),artwork: Object.freeze({kind: "prepared-artwork"}),dataAssets: Object.freeze({kind: "prepared-content"})})}),\n'
if '    th143:' not in text:text=text.replace('  th15: Object.freeze({',content+'  th15: Object.freeze({',1)
path.write_text(text,encoding='utf-8',newline='\n')
path=site/'launcher/scripts/package-server.mjs';text=path.read_text(encoding='utf-8')
# An embedded soundtrack lives in the verified base DATA object, so there is
# no optional OGG album to publish. Other products keep their existing path.
text=text.replace('if (modes.has("ogg")) {\n      const pack = entry.music?.ogg;', 'if (modes.has("ogg") && (entry.music?.ogg || !("embeddedOgg" in product.musicRuntime && product.musicRuntime.embeddedOgg))) {\n      const pack = entry.music?.ogg;')
path.write_text(text,encoding='utf-8',newline='\n')
path=site/'launcher/app/components/launcher/products.ts';text=path.read_text(encoding='utf-8').replace("th14:'针',","th14:'针',th143:'弹',");path.write_text(text,encoding='utf-8',newline='\n')
print(json.dumps(dict(game='th143',dataLayout=layout)))
