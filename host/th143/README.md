# TH143 production runtime

TH143 V154 uses the standard Launcher product, managed Package Store, immutable
Runtime generation and IDBFS save contracts. The native WebAssembly core is
byte-identical to the accepted behavioral build.

The standard entry is `https://wth.saop.cc/?game=th143`.

`launcher-adapter.mjs` owns the navigation epoch, input mapping, resource
ownership, lifecycle and file protocol. `launcher-file-store.mjs` implements the
accepted transactional file API on `/savesth143`, database version 21,
`FILE_DATA`. Score, configuration, replays and scene previews use that store.
Launcher save transfer includes `scoreth143.dat` and `th143.cfg`; scene preview
files remain in local IDBFS. File mutations require a closed game or a file-only
Runtime, preserving native in-memory replay and save ownership.

The managed content package contains the verified build plan, 802 resource
blobs and Noto Sans JP. The original PCM soundtrack is embedded in DATA and uses
the Launcher's existing embedded soundtrack policy. BGM and sound-effect volume
controls scale the corresponding ordered mixer inputs. The font license is
published as `font-license.json` beside the Runtime.

Build with `tools/th143-launcher-build.py`, using the accepted static content as
`--accepted` and a Launcher source checkout as `--site-source`. Register the
product with `tools/th143-register-launcher.py`. That registration uses the
existing `retail-memory` directory adapter contract; `package-server.mjs`
publishes the managed package and immutable generation, and
`verify-server-build.mjs` validates the resulting complete site.

`tools/th143-launcher-contract-check.mjs` checks the shared save namespace,
batch snapshots, transaction aborts, replay operations, path boundaries, epoch
isolation and touch input. It uses `fake-indexeddb` from the Launcher test
dependencies.

Native source publication: `runtimes/th143/production/source-manifest.json`.
Game content, fonts, compiled WASM and personal saves are deployed separately
from Git source publication.
