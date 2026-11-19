"""Register TH06nc through the canonical product/content/workspace catalogs."""
import argparse,hashlib,json,re
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('site',type=Path);p.add_argument('--content',type=Path,required=True);args=p.parse_args();site=args.site
layout='sha256-'+hashlib.sha256(b'th06nc/content/1:indexed-independent-gzip:2026-11').hexdigest()
path=site/'common/contracts/product-catalog.mjs';text=path.read_text(encoding='utf-8')
product='''    th06nc: Object.freeze({
        testOnly: true, buildOptIn: true,
        number: "06nc", title: "東方紅魔郷 New Classic", subtitle: "the Embodiment of Scarlet Devil · New Classic",
        cardArtwork: "th06nc-card.webp",
        storage: Object.freeze({saveRoot: "/savesth06nc", scoreFile: "score.dat", configFiles: Object.freeze(["th06.cfg", "th06.env", "achievements.json"])}),
        runtime: "./runtime/th06nc/th06nc.html", runtimeFileLayout: "directory",
        runtimeAssets: Object.freeze(["th06nc.html", "manifest.json", "launcher-adapter.mjs", "directory-keyboard.mjs", "game.mjs"]), requiredShared: Object.freeze([]),
        runtimeResourceTransport: "resources", dataProvider: "retail-memory",
        musicCapabilities: Object.freeze({midi: false}), musicRuntime: Object.freeze({localOggConfigureMode: "runtime-selection", requiresCompleteOgg: true}),
        touchFire: TOGGLE_TOUCH_FIRE,
        support: Object.freeze({highRefreshRate: false, sourceRepository: "https://github.com/AdingApkgg/thp"}),
        package: Object.freeze({dataFileId: "game-data", dataTarget: "/th06nc.data", musicSourceDirectories: Object.freeze({ogg: "music"}), musicMounts: Object.freeze({ogg: "/music"})}),
        replay: Object.freeze({prefix: "th6"}), features: Object.freeze({thprac: false, languages: false, focusHitbox: false}),
    }),
'''
if '    th06nc:' in text:
 start=text.index('    th06nc:');end=text.index('    th07: Object.freeze({',start);text=text[:start]+text[end:]
text=text.replace('    th07: Object.freeze({',product+'    th07: Object.freeze({',1)
# Preserve the already-published TH14 multiplayer runtime when validating the
# complete site; it must not depend on a private verifier fork.
start=text.index('    th14: Object.freeze({');end=text.index('    th15: Object.freeze({',start)
if 'multiplayerRuntime:' not in text[start:end]:text=text[:start]+text[start:end].replace('        runtime: "./runtime/th14/th14.html",','        runtime: "./runtime/th14/th14.html",\n        multiplayerRuntime: "./runtime/th14/multiplayer/th14.html",')+text[end:]
path.write_text(text,encoding='utf-8',newline='\n')
path=site/'common/contracts/product-catalog.d.mts';text=path.read_text(encoding='utf-8')
declaration='''    th06nc: Readonly<{
        testOnly: true; buildOptIn: true; number: "06nc"; title: string; subtitle: string; cardArtwork: "th06nc-card.webp";
        storage: Readonly<{saveRoot: "/savesth06nc";scoreFile: "score.dat";configFiles: readonly string[]}>;
        runtime: "./runtime/th06nc/th06nc.html";runtimeFileLayout: "directory";runtimeAssets: readonly string[];requiredShared: readonly string[];
        runtimeResourceTransport: "resources";dataProvider: "retail-memory";
        musicCapabilities: Readonly<{midi: false}>;musicRuntime: Readonly<{localOggConfigureMode: "runtime-selection";requiresCompleteOgg: true}>;
        touchFire: Readonly<{mode: "toggle";labelKey: "touch.tapToggle"}>;
        support: Readonly<{highRefreshRate: false;sourceRepository: string}>;
        package: Readonly<{dataFileId: "game-data";dataTarget: "/th06nc.data";musicSourceDirectories: Readonly<{ogg: "music"}>;musicMounts: Readonly<{ogg: "/music"}>}>;
        replay: Readonly<{prefix: "th6"}>;features: Readonly<{thprac: false;languages: false;focusHitbox: false}>;
    }>;
'''
if '    th06nc:' in text:
 start=text.index('    th06nc:');end=text.index('    th07: Readonly<{',start);text=text[:start]+text[end:]
text=text.replace('    th07: Readonly<{',declaration+'    th07: Readonly<{',1)
path.write_text(text,encoding='utf-8',newline='\n')
path=site/'launcher/lib/content-definition.mjs';text=path.read_text(encoding='utf-8');tracks=sorted((p.name for p in (args.content/'music').glob('*.ogg')),key=lambda name:(name.startswith('bgm2_'),name))
content='    th06nc: Object.freeze({original: Object.freeze({files: Object.freeze(["th06nc.data"])}), dataLayout: '+json.dumps(layout)+', music: Object.freeze({ogg: Object.freeze({mount: "/music",files: Object.freeze('+json.dumps(tracks)+')})}),hostPreparation: Object.freeze({preparedContent: Object.freeze({directory: "content",markerFiles: Object.freeze(["th06nc.data"])}),artwork: Object.freeze({kind: "prepared-artwork"}),ogg: Object.freeze({kind: "prepared-content"}),dataAssets: Object.freeze({kind: "prepared-content"})})}),\n'
text=re.sub(r'^    th06nc:.*\n','',text,flags=re.M)
text=text.replace('  th07: Object.freeze({',content+'  th07: Object.freeze({',1)
path.write_text(text,encoding='utf-8',newline='\n')
path=site/'launcher/config/workspace.json';data=json.loads(path.read_text());data['repositories']['th06nc']='external/th06nc';path.write_text(json.dumps(data,indent=2)+'\n')
path=site/'launcher/app/components/launcher/products.ts';text=path.read_text(encoding='utf-8');text=text.replace("th06nc:'红NC',",'').replace("th06:'红',","th06:'红',th06nc:'红NC',");path.write_text(text,encoding='utf-8',newline='\n')
path=site/'launcher/app/components/launcher/book-preferences.ts';text=path.read_text(encoding='utf-8');text=text.replace('/^th[a-z]/i','/^th(?:[a-z]|\\d+[a-z])/i');path.write_text(text,encoding='utf-8',newline='\n')
path=site/'launcher/tests/test-product-catalog.mjs';text=path.read_text(encoding='utf-8');text=text.replace('"th06", "th07",','"th06", "th06nc", "th07",').replace('"hsob", "th13",','"hsob", "th06nc", "th13",').replace('th06: true, th07:', 'th06: true, th06nc: false, th07:');path.write_text(text,encoding='utf-8',newline='\n')
print(json.dumps(dict(game='th06nc',dataLayout=layout,musicFiles=len(tracks))))
