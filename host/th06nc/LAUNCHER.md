# TH06nc Launcher integration

TH06nc is a separate product in the canonical Launcher catalog. The source
repository is `AdingApkgg/thp`; the site workspace registers it as
`external/th06nc`. Engine code and content are packaged separately.

1. Run `prepare-content.py --artifacts PATH --output CONTENT` on the output of
   the TH06nc asset preparers. This creates `th06nc.data` and a flat `music/`
   directory. Game assets stay outside Git.
2. Run `tools/th06nc-launcher-register.py SITE_SOURCE --content CONTENT` to
   register the product, content layout, workspace source and library label.
3. Run `tools/th06nc-launcher-build.py --site-source SITE_SOURCE --output BUILD`.
   It emits the closed directory Runtime and its file identities, using the
   site's shared keyboard and direct-input bridges.
4. Build the site's React frontend from the same catalog. Package selected games
   with the standard `launcher/scripts/package-server.mjs` entry, supplying
   `--th06nc-build`, `--th06nc-assets`, `--th06nc-ogg`, normalized artwork, shared
   fonts, a feature configuration and the previous verified site.
5. Run `verify-server-build.mjs` against the candidate, then exercise the root
   library, package installation, first frame, input and user files in a browser.

The adapter validates origin, game and navigation epoch. It obtains installed
DATA through `__eaglerPrepareManagedRuntimeDataV1`, consumes managed music
resources, and stores files in `/savesth06nc`, using the shared IDBFS version 21
`FILE_DATA` schema. Original standalone saves retain their original database.

The dated standalone deployment records describe the earlier direct-directory
publication. They do not attest root-library integration. Use the Launcher
acceptance record for that scope.
