# TH06nc Launcher integration

TH06nc is a separate product in the canonical Launcher catalog. The source
repository is `AdingApkgg/thp`; the site workspace registers it as
`external/th06nc`. Engine code and content are packaged separately.

The site integration patch is based on `AdingApkgg/eagler-touhou` commit
`4ad1867ed6e825bb2f91b71ad73536ec106c608c`. Apply
`host/th06nc/site-integration.patch` to that clean checkout before the steps
below. It includes the combined product catalog, validated offline publication
metadata cache and static transport policy. TH143 keeps its existing published
Runtime and content identities.

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
   Include the global favicon and all `pwa/` icons in the normalized artwork
   directory. The site's `prepare-host-artwork.py` derives these from its brand
   portrait; they are required by the published document independently of the
   selected games.
5. Run `verify-server-build.mjs` against the candidate, then exercise the root
   library, package installation, first frame, input and user files in a browser.

The adapter validates origin, game and navigation epoch. It obtains installed
DATA through `__eaglerPrepareManagedRuntimeDataV1`, consumes managed music
resources, and stores files in `/savesth06nc`, using the shared IDBFS version 21
`FILE_DATA` schema. Original standalone saves retain their original database.

Publication compares every retained game's full Site Manifest entry and shared
configuration with the current production release. A concurrent release change
stops promotion. The canonical verifier checks the complete candidate before
activation; the managed service uses that same verifier on subsequent starts.

The dated standalone deployment records describe the earlier direct-directory
publication. They do not attest root-library integration. Use the Launcher
acceptance record for that scope.
