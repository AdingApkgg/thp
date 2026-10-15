"""Recompute stored ordinary TH14 loading evidence, without running the game.

Original assets, snapshots and raw mismatches remain private. Declared clocks,
CPU textures, stopped audio and no-output GPU calls are not hardware evidence.
"""
import hashlib
import importlib.util
import json
import struct
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'artifacts/th14'
OUT = ROOT / 'docs/porting/th14-ordinary-loading-observed-oct15.json'
SHA = lambda b: hashlib.sha256(b).hexdigest()
BINDINGS = {'artifacts/archive-differential/th14.json': {'bytes': 33614, 'sha256': '4cd201cae19e606e6ac258bf2241a9bb7ae9adde811bae9c3ff7d1513ffcdf78'}, 'artifacts/th14/main-during-sixty-wait-oct15/checkpoint/manifest.json': {'bytes': 178815, 'sha256': '9cd865a3bffc9f5f63798dd08554259e6c601b9ae9761717052b71ffbb79f0a4'}, 'artifacts/th14/main-during-sixty-wait-oct15/checkpoint/runtime-state.json': {'bytes': 8211, 'sha256': 'dda4da3c19fa8fbb7bf66dca050ad23e88e37deb9deae3af711644860b04deae'}, 'artifacts/th14/main-during-sixty-wait-oct15/checkpoint.py': {'bytes': 7199, 'sha256': '0a3aafc323aa32f6f4380eef53afc01593671afbc9f085b981aa62d379822136'}, 'artifacts/th14/main-during-sixty-wait-oct15/cooperative_worker.py': {'bytes': 18172, 'sha256': '138a275695d22ca805fdc15114fe3ac7df5b7a6c13c7ee2ec729a8c22ba64e12'}, 'artifacts/th14/main-during-sixty-wait-oct15/main_locks.py': {'bytes': 1451, 'sha256': '3ac11fd1976ecf424ac1ec4101950b85db632a1f1eb8c2462bc51844a00c9218'}, 'artifacts/th14/main-during-sixty-wait-oct15/plan.json': {'bytes': 4821, 'sha256': 'bfd0f27131c51e9de21ba0d7e5f69e47b8ecd175daee13a0f37fc23674dd8889'}, 'artifacts/th14/main-during-sixty-wait-oct15/receipt.json': {'bytes': 555990, 'sha256': '562a39cab6d7a40133af0ca91e370da165144047e1530ba174928fe13892c088'}, 'artifacts/th14/main-during-sixty-wait-oct15/silent_audio.py': {'bytes': 2130, 'sha256': '3969290b1fb8e5ab1c67337648538e48de8bd188a0e397fd29b80ccebdfa0e42'}, 'artifacts/th14/main-during-sixty-wait-oct15/slice.py': {'bytes': 18171, 'sha256': 'b8866d71ac0db42a2ac33c9d04a31800f6ad02d3020130e30322f24e9cc31df4'}, 'artifacts/th14/main-pumps-background-after-sixty-oct15/checkpoint/manifest.json': {'bytes': 204836, 'sha256': '3f35b58367f1429d44c432224ef330a4a699b23b1f142f368b7fdda97b161ada'}, 'artifacts/th14/main-pumps-background-after-sixty-oct15/checkpoint/runtime-state.json': {'bytes': 29669, 'sha256': 'bfb8c87a4d35f591d33887fe5b54c9f137df0ea8835dd8a5ef0b57cdfd5e716f'}, 'artifacts/th14/main-pumps-background-after-sixty-oct15/checkpoint.py': {'bytes': 7560, 'sha256': 'ad32a8909450ad80b3ce01627666d5bb0eb15bf0ef0868603ba52d4e920dd7e2'}, 'artifacts/th14/main-pumps-background-after-sixty-oct15/cooperative_worker.py': {'bytes': 18172, 'sha256': '138a275695d22ca805fdc15114fe3ac7df5b7a6c13c7ee2ec729a8c22ba64e12'}, 'artifacts/th14/main-pumps-background-after-sixty-oct15/cpu_textures.py': {'bytes': 7264, 'sha256': '8049abcb80e8cab44a01c4083f87f71b030cff40d92c9b8a979e1a01a5724144'}, 'artifacts/th14/main-pumps-background-after-sixty-oct15/main_locks.py': {'bytes': 1451, 'sha256': 'bb718c7506e3e4c5f5a6eca360e065bcbad5f0d042cd176f065fc9c47ce58821'}, 'artifacts/th14/main-pumps-background-after-sixty-oct15/plan.json': {'bytes': 4715, 'sha256': '9a5e34a4cb258c0dda1ed8ffd0e62465d91a9afd59fcffdbbf97b34895820b76'}, 'artifacts/th14/main-pumps-background-after-sixty-oct15/receipt.json': {'bytes': 1123795, 'sha256': '8da1cf0a0936b9edb2964dd2eb8e9e8d6716145ba4868ee231b1829376269366'}, 'artifacts/th14/main-pumps-background-after-sixty-oct15/silent_audio.py': {'bytes': 2130, 'sha256': '3969290b1fb8e5ab1c67337648538e48de8bd188a0e397fd29b80ccebdfa0e42'}, 'artifacts/th14/main-pumps-background-after-sixty-oct15/slice.py': {'bytes': 18487, 'sha256': 'd5e5cd1a2ef88fa381f0900ff80fd149872930e90080766d91721a1dba66d1d3'}, 'artifacts/th14/main-pumps-enemy-after-sixty-oct15/checkpoint/manifest.json': {'bytes': 217208, 'sha256': 'f20ce63b9af1eadac8279a23ecc8923dfebca9f4b0e9d56aac8d3eb7644f54a8'}, 'artifacts/th14/main-pumps-enemy-after-sixty-oct15/checkpoint/runtime-state.json': {'bytes': 23378, 'sha256': '99dba451a1c68dc4d2b36a917bccf74db03be3c0dd5a313cf4c54d81da5c6a2b'}, 'artifacts/th14/main-pumps-enemy-after-sixty-oct15/checkpoint.py': {'bytes': 7560, 'sha256': '513804e2d110594ab52f439da226c4d8da0061ea295e3958ea4b1d7df9447c9c'}, 'artifacts/th14/main-pumps-enemy-after-sixty-oct15/cooperative_worker.py': {'bytes': 18172, 'sha256': '138a275695d22ca805fdc15114fe3ac7df5b7a6c13c7ee2ec729a8c22ba64e12'}, 'artifacts/th14/main-pumps-enemy-after-sixty-oct15/cpu_textures.py': {'bytes': 7511, 'sha256': '3245702c1442abaad4d6fa4f5d8ae7a3eb7d69d3066dcb4fdd815724a2e9dcb5'}, 'artifacts/th14/main-pumps-enemy-after-sixty-oct15/main_locks.py': {'bytes': 1451, 'sha256': 'bb718c7506e3e4c5f5a6eca360e065bcbad5f0d042cd176f065fc9c47ce58821'}, 'artifacts/th14/main-pumps-enemy-after-sixty-oct15/plan.json': {'bytes': 4724, 'sha256': 'b1bd7f4c5b7e9ce8e7d6b3fa135812732da86c828bba95f666a9c5febab3d2d1'}, 'artifacts/th14/main-pumps-enemy-after-sixty-oct15/receipt.json': {'bytes': 568301, 'sha256': '9bc78c8ebdc503b1ebf4659a5c00d3f8312b7b3c1531159bae821bed6ba760fa'}, 'artifacts/th14/main-pumps-enemy-after-sixty-oct15/silent_audio.py': {'bytes': 2130, 'sha256': '3969290b1fb8e5ab1c67337648538e48de8bd188a0e397fd29b80ccebdfa0e42'}, 'artifacts/th14/main-pumps-enemy-after-sixty-oct15/slice.py': {'bytes': 18476, 'sha256': '9f663768fddef6565c7fffd2c02546c6c5313eace6537f2c0bfb044c193b442c'}, 'artifacts/th14/main-pumps-logo-after-sixty-oct15/checkpoint/manifest.json': {'bytes': 185981, 'sha256': 'd54dbbf7997ea1893d608ec34dfb4d6c2b2a66e51bebe82613c4abf7f63addf4'}, 'artifacts/th14/main-pumps-logo-after-sixty-oct15/checkpoint/runtime-state.json': {'bytes': 15969, 'sha256': '3603d4ea8b3814bdf9ab272dc69fb53e2619de3f39035d87d82b87446651644f'}, 'artifacts/th14/main-pumps-logo-after-sixty-oct15/checkpoint.py': {'bytes': 7560, 'sha256': '74710d9293c24ca75b19dec03dd1e74f7ee5157073e569c2292f948bbebbb3ef'}, 'artifacts/th14/main-pumps-logo-after-sixty-oct15/cooperative_worker.py': {'bytes': 18172, 'sha256': '138a275695d22ca805fdc15114fe3ac7df5b7a6c13c7ee2ec729a8c22ba64e12'}, 'artifacts/th14/main-pumps-logo-after-sixty-oct15/cpu_textures.py': {'bytes': 7250, 'sha256': '6a392ba4efa0896a27f73e579c538d57fa196fc01956a7bdc2a415c0cdb51e87'}, 'artifacts/th14/main-pumps-logo-after-sixty-oct15/main_locks.py': {'bytes': 1451, 'sha256': 'bb718c7506e3e4c5f5a6eca360e065bcbad5f0d042cd176f065fc9c47ce58821'}, 'artifacts/th14/main-pumps-logo-after-sixty-oct15/plan.json': {'bytes': 4709, 'sha256': 'f7c82cc971c7316a6ec904c7c400c6e76d58357a6ac6d5db561f232ea9ce9913'}, 'artifacts/th14/main-pumps-logo-after-sixty-oct15/receipt.json': {'bytes': 387536, 'sha256': 'ec706a9348bb7df3ada941462732c0c8e5b6c4a47e67e1a2314d4d0872c3c25f'}, 'artifacts/th14/main-pumps-logo-after-sixty-oct15/silent_audio.py': {'bytes': 2130, 'sha256': '3969290b1fb8e5ab1c67337648538e48de8bd188a0e397fd29b80ccebdfa0e42'}, 'artifacts/th14/main-pumps-logo-after-sixty-oct15/slice.py': {'bytes': 18463, 'sha256': '99f83ebd3fca058a0abcaf0015b79b380fd97d04b1d56dc588e242bf6b17b647'}, 'artifacts/th14/main-pumps-music-after-sixty-oct15/checkpoint/manifest.json': {'bytes': 267646, 'sha256': '64a82df7ad74ba451eb9ee6215d19243ee481e4d0e964d1d68535273570d3b3b'}, 'artifacts/th14/main-pumps-music-after-sixty-oct15/checkpoint/runtime-state.json': {'bytes': 32805, 'sha256': '1c0f63f627245ea0d65205118c4c6f2670fd83ddee30b94afdd44aa2a1dafd3b'}, 'artifacts/th14/main-pumps-music-after-sixty-oct15/checkpoint.py': {'bytes': 7675, 'sha256': '12d87f52c64cca17a428c9388c4bb5808a8023ab381c6803f78f0af45a48e840'}, 'artifacts/th14/main-pumps-music-after-sixty-oct15/cooperative_worker.py': {'bytes': 18172, 'sha256': '138a275695d22ca805fdc15114fe3ac7df5b7a6c13c7ee2ec729a8c22ba64e12'}, 'artifacts/th14/main-pumps-music-after-sixty-oct15/main_locks.py': {'bytes': 1451, 'sha256': '3ac11fd1976ecf424ac1ec4101950b85db632a1f1eb8c2462bc51844a00c9218'}, 'artifacts/th14/main-pumps-music-after-sixty-oct15/plan.json': {'bytes': 4859, 'sha256': '7238daba03f9965e69f333b2c63b79a11fc2e97d192c7485717279d448d74fe0'}, 'artifacts/th14/main-pumps-music-after-sixty-oct15/receipt.json': {'bytes': 819502, 'sha256': '8fa441f7c98c3d97cbf0eba14b7bd080452962514d27eb103d39f718703fab75'}, 'artifacts/th14/main-pumps-music-after-sixty-oct15/silent_audio.py': {'bytes': 2130, 'sha256': '3969290b1fb8e5ab1c67337648538e48de8bd188a0e397fd29b80ccebdfa0e42'}, 'artifacts/th14/main-pumps-music-after-sixty-oct15/slice.py': {'bytes': 17800, 'sha256': '665f3e2f6d4e071f78625c49022a191c15ed399fae95c4b54a30969a5b64871d'}, 'artifacts/th14/main-pumps-stage-enemy-after-sixty-oct15/checkpoint/manifest.json': {'bytes': 266172, 'sha256': '9f32da4078f1100985f3f34f22092b31b44020cf1d16807b22075c871da17a52'}, 'artifacts/th14/main-pumps-stage-enemy-after-sixty-oct15/checkpoint/runtime-state.json': {'bytes': 47607, 'sha256': 'edf539495172600f332347a682763d5451249f15e652974962acf45e4eee751e'}, 'artifacts/th14/main-pumps-stage-enemy-after-sixty-oct15/checkpoint.py': {'bytes': 7560, 'sha256': '18bbeae70ff6f42dff9f8b3729dc4ad3294f32e4774e130beb7aff3cc3d92c8b'}, 'artifacts/th14/main-pumps-stage-enemy-after-sixty-oct15/cooperative_worker.py': {'bytes': 18172, 'sha256': '138a275695d22ca805fdc15114fe3ac7df5b7a6c13c7ee2ec729a8c22ba64e12'}, 'artifacts/th14/main-pumps-stage-enemy-after-sixty-oct15/cpu_textures.py': {'bytes': 7719, 'sha256': 'fb0b632a5090f9e974078c76be051db188d7cdeaf6e6b7a7a7472bf2added495'}, 'artifacts/th14/main-pumps-stage-enemy-after-sixty-oct15/main_locks.py': {'bytes': 1451, 'sha256': '3ac11fd1976ecf424ac1ec4101950b85db632a1f1eb8c2462bc51844a00c9218'}, 'artifacts/th14/main-pumps-stage-enemy-after-sixty-oct15/plan.json': {'bytes': 4727, 'sha256': 'f94f80e40bf87d3b2ecb2129b075622459f114360378a2f5e0d69bd81b89f900'}, 'artifacts/th14/main-pumps-stage-enemy-after-sixty-oct15/receipt.json': {'bytes': 3075693, 'sha256': 'db417e1ca2df2959a4f225ac9af1c8e5c2fd1e6c55e033f4fff036f9037cb005'}, 'artifacts/th14/main-pumps-stage-enemy-after-sixty-oct15/silent_audio.py': {'bytes': 2130, 'sha256': '3969290b1fb8e5ab1c67337648538e48de8bd188a0e397fd29b80ccebdfa0e42'}, 'artifacts/th14/main-pumps-stage-enemy-after-sixty-oct15/slice.py': {'bytes': 18641, 'sha256': '83e23da4cdd17293c59e492c92187e5ce37357257766031233e10e699f28352a'}, 'artifacts/th14/screen-camera-production-build-oct14/build-result.json': {'bytes': 229508, 'sha256': '26fc6f89e33f19bcc48b57d58ebb8582fdc79688c0166d27b01a620e5a5dfb09'}, 'artifacts/th14/sixty-main-current-core-probe-oct15/check.mjs': {'bytes': 8595, 'sha256': 'aa2a23d68bb9f17e0f83d76902397a67b78516b15b45df3e7ecdde7a39dfb3ef'}, 'artifacts/th14/sixty-main-current-core-probe-oct15/fixture.cpp': {'bytes': 2483, 'sha256': '44c02e8920fdfd144686e9a8769cc7849f092ebd1103c099bd1232ccc20a5f74'}, 'artifacts/th14/sixty-main-current-core-probe-oct15/mode-0-differences.json': {'bytes': 2576928, 'sha256': 'ca707853bcfa2e49de693e4c4ac2a33e972bb224e10359b9692b962be271c3df'}, 'artifacts/th14/sixty-main-current-core-probe-oct15/mode-0-owners.u8': {'bytes': 9703, 'sha256': 'd7b84b64c77d075104ecb3e805d4de23a60aeb7933b3607cc664d03f8ab21599'}, 'artifacts/th14/sixty-main-current-core-probe-oct15/mode-0-queue.json': {'bytes': 3, 'sha256': '37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570'}, 'artifacts/th14/sixty-main-current-core-probe-oct15/mode-0-selected.u32': {'bytes': 1241984, 'sha256': '48286e9d7a1b5ac4864cd905ee4dfd3865eeb81615fb05c096d6dafa5ec3a27d'}, 'artifacts/th14/sixty-main-current-core-probe-oct15/mode-1-differences.json': {'bytes': 2575872, 'sha256': 'c160841d00a2233da92fb82825ced0494de3cb3ab73f58c75c2dcc085e3b4457'}, 'artifacts/th14/sixty-main-current-core-probe-oct15/mode-1-owners.u8': {'bytes': 9703, 'sha256': 'b7407a56c303030e1366645ad3cb2d98bba745185d9f3b69062308a1d9b05014'}, 'artifacts/th14/sixty-main-current-core-probe-oct15/mode-1-queue.json': {'bytes': 649, 'sha256': '523a0098b6af1d3cda5d3a574f3aa6c989ea3bd23e6d4466aaa2d2baea0391a8'}, 'artifacts/th14/sixty-main-current-core-probe-oct15/mode-1-selected.u32': {'bytes': 1241984, 'sha256': '48286e9d7a1b5ac4864cd905ee4dfd3865eeb81615fb05c096d6dafa5ec3a27d'}, 'artifacts/th14/sixty-main-current-core-probe-oct15/native-input-bindings.json': {'bytes': 9954, 'sha256': 'd4bebef78f24dcc8457eda7166337df68030ba9cc05054e8d944a2fc3d314212'}, 'artifacts/th14/sixty-main-current-core-probe-oct15/native-owner-presence.u8': {'bytes': 9703, 'sha256': 'b7407a56c303030e1366645ad3cb2d98bba745185d9f3b69062308a1d9b05014'}, 'artifacts/th14/sixty-main-current-core-probe-oct15/native-selected-state.u32': {'bytes': 1241984, 'sha256': '9ff690f65b146fef74fcca9f0c168e5428190bb19c82d6a0424d8d38981c1ddb'}, 'artifacts/th14/sixty-main-current-core-probe-oct15/native-word-availability.u8': {'bytes': 310496, 'sha256': '8c17e38b66e0db007d13dd7cdb2996c3c58dd7558b5298e6c282cb7f4acbebf3'}, 'artifacts/th14/sixty-main-current-core-probe-oct15/ordinary-player-rows.json': {'bytes': 36317, 'sha256': '0c943bcd8b43ef45b888d9ede7058ea1eb5641a6304077e374ee3ec75acf8841'}, 'artifacts/th14/sixty-main-current-core-probe-oct15/probe.wasm': {'bytes': 1450056, 'sha256': 'ef38c265cec0e62968871595cd3b4cedad005461050d2c37b156a351aef78e49'}, 'artifacts/th14/sixty-main-current-core-probe-oct15/receipt.json': {'bytes': 19161, 'sha256': 'b1c312a74774adbcbea288561fede98d8eeca4c81da4845cd4f959204d91b0bd'}, 'artifacts/th14/warm-worker-checkpoint-prepared-oct15/run-oct15/original-prefix.jsonl': {'bytes': 4403530, 'sha256': 'befb7b0980869fabb6264492f86c3910ad075da662a8086f32fe2b5b4a8b6fad'}, 'artifacts/th14/worker-after-background-after-sixty-oct15/checkpoint.py': {'bytes': 7560, 'sha256': '513804e2d110594ab52f439da226c4d8da0061ea295e3958ea4b1d7df9447c9c'}, 'artifacts/th14/worker-after-background-after-sixty-oct15/cooperative_worker.py': {'bytes': 18172, 'sha256': '138a275695d22ca805fdc15114fe3ac7df5b7a6c13c7ee2ec729a8c22ba64e12'}, 'artifacts/th14/worker-after-background-after-sixty-oct15/plan.json': {'bytes': 6626, 'sha256': '8cd396f2259af0c4893b6952fb496d431a6e9b92659f0f64cae111837667869b'}, 'artifacts/th14/worker-after-background-after-sixty-oct15/resume.py': {'bytes': 30690, 'sha256': 'fa5e06ca5479eca62ef1163a05638711fdb113b865ade326139769a88dd0b315'}, 'artifacts/th14/worker-after-background-after-sixty-oct15/run/checkpoint/manifest.json': {'bytes': 206591, 'sha256': 'ad3605e069c7439999724ac5f3351c8b77a04967cd286030fd282cb1185849aa'}, 'artifacts/th14/worker-after-background-after-sixty-oct15/run/checkpoint/runtime-state.json': {'bytes': 30739, 'sha256': '3bc572b7dd0514b5ba2f30c0f610381acb1058ddb297690da21f2d1b410a8739'}, 'artifacts/th14/worker-after-background-after-sixty-oct15/run/decoded-0.bin': {'bytes': 21244, 'sha256': '82925af3fd3dacbdaedda3dee9be2801ea664a8c44c99d180861714062076ee3'}, 'artifacts/th14/worker-after-background-after-sixty-oct15/run/decoded-1.bin': {'bytes': 718412, 'sha256': '89f12708a0cf4567dd420b15666f048208154e77df123154a6302ca5056836e6'}, 'artifacts/th14/worker-after-background-after-sixty-oct15/run/receipt.json': {'bytes': 18750, 'sha256': '0453923c58c3d224fc3304bed8dedd0efaa4009609268f2b29febb9d856948e6'}, 'artifacts/th14/worker-after-enemy-after-sixty-oct15/checkpoint.py': {'bytes': 7560, 'sha256': '18bbeae70ff6f42dff9f8b3729dc4ad3294f32e4774e130beb7aff3cc3d92c8b'}, 'artifacts/th14/worker-after-enemy-after-sixty-oct15/cooperative_worker.py': {'bytes': 18172, 'sha256': '138a275695d22ca805fdc15114fe3ac7df5b7a6c13c7ee2ec729a8c22ba64e12'}, 'artifacts/th14/worker-after-enemy-after-sixty-oct15/plan.json': {'bytes': 6704, 'sha256': 'eba7e96d64c12ac32219e23bf7d7e2d24285a23fc84fa55b8c6b8ca5968cb5d0'}, 'artifacts/th14/worker-after-enemy-after-sixty-oct15/resume.py': {'bytes': 30667, 'sha256': 'a7cf34d356c768add9c57fde81a97a995e6bc68347554b70292d4f28de4d776a'}, 'artifacts/th14/worker-after-enemy-after-sixty-oct15/run/checkpoint/manifest.json': {'bytes': 218363, 'sha256': '8f026e8f61588f27953991c6a1ce6db1ff39f358cf1c257d0997e7f3d6521a57'}, 'artifacts/th14/worker-after-enemy-after-sixty-oct15/run/checkpoint/runtime-state.json': {'bytes': 15266, 'sha256': '547a54af150ceeb84c805f36176ade4b5f91d74aa11d6607ec9fc6fc42f2df98'}, 'artifacts/th14/worker-after-enemy-after-sixty-oct15/run/decoded-0.bin': {'bytes': 4669024, 'sha256': '0a4c10fca0a4ed65fe8fa65b58364ceef0a2713a6b2c5b5528170bc51c539d5c'}, 'artifacts/th14/worker-after-enemy-after-sixty-oct15/run/receipt.json': {'bytes': 10948, 'sha256': '414faadff9616a2e731f6f90864d161689db6d20e425ff8987931dcf57fd3ea9'}, 'artifacts/th14/worker-after-logo-after-sixty-oct15/checkpoint.py': {'bytes': 7560, 'sha256': 'ad32a8909450ad80b3ce01627666d5bb0eb15bf0ef0868603ba52d4e920dd7e2'}, 'artifacts/th14/worker-after-logo-after-sixty-oct15/cooperative_worker.py': {'bytes': 18172, 'sha256': '138a275695d22ca805fdc15114fe3ac7df5b7a6c13c7ee2ec729a8c22ba64e12'}, 'artifacts/th14/worker-after-logo-after-sixty-oct15/plan.json': {'bytes': 7355, 'sha256': '78399bdb53501192937829da6760679b4d4b6344c888718ca0e88984327e79ca'}, 'artifacts/th14/worker-after-logo-after-sixty-oct15/resume.py': {'bytes': 30768, 'sha256': '971457a9a6f1424a007dc8bdd39d7e9221c597e6ab93f460cb0afd37859b9cad'}, 'artifacts/th14/worker-after-logo-after-sixty-oct15/run/checkpoint/manifest.json': {'bytes': 187717, 'sha256': '17d94b473bcdd6315cf123eb9b88bd5289055aa64a11ee2555c6a842b9732222'}, 'artifacts/th14/worker-after-logo-after-sixty-oct15/run/checkpoint/runtime-state.json': {'bytes': 19655, 'sha256': 'fd5d09a77fed68785c325212ae65a8ed36b88e11447cbda09367a894b7649553'}, 'artifacts/th14/worker-after-logo-after-sixty-oct15/run/decoded-0.bin': {'bytes': 1280, 'sha256': '195363bab2bb2ee0392f0c499df8059168dd14adfdf3035dc07fb79d36fed2c9'}, 'artifacts/th14/worker-after-logo-after-sixty-oct15/run/decoded-1.bin': {'bytes': 2224, 'sha256': 'd6a9ca43c1a3018d898dcfff5e2134e383ea7f4cef7b3452caccbef722559558'}, 'artifacts/th14/worker-after-logo-after-sixty-oct15/run/decoded-2.bin': {'bytes': 1688960, 'sha256': '8b01648d5c0602eb63b86692b3620fd3e38c7afca20a33bdcc9917ba938fe6bf'}, 'artifacts/th14/worker-after-logo-after-sixty-oct15/run/receipt.json': {'bytes': 17541, 'sha256': '57cb369b714630fa1a3b7d81e1a1fc3d7facc4ff9c9816e2560f9ce989c0e1a5'}, 'artifacts/th14/worker-after-music-after-sixty-oct15/checkpoint.py': {'bytes': 8125, 'sha256': '348e6cb4ef52cf3dc26b8664f6a534504405bfa89108e0a15c68d15c243692c6'}, 'artifacts/th14/worker-after-music-after-sixty-oct15/cooperative_worker.py': {'bytes': 18172, 'sha256': '138a275695d22ca805fdc15114fe3ac7df5b7a6c13c7ee2ec729a8c22ba64e12'}, 'artifacts/th14/worker-after-music-after-sixty-oct15/plan.json': {'bytes': 8067, 'sha256': 'fc22cdd0010a2bb6991b5d84474cb2104a069bffc1473f7c8ba4f8ff92f93595'}, 'artifacts/th14/worker-after-music-after-sixty-oct15/resume.py': {'bytes': 31869, 'sha256': '3e9f4211385ee809b132d6c0326b85571c19aae6efefb0f0108511ed538457f8'}, 'artifacts/th14/worker-after-music-after-sixty-oct15/run/checkpoint/manifest.json': {'bytes': 267912, 'sha256': '8499f20b1ec2f58dc2b3d2056185cbe61c79aa5bbd86c46f5fb3d33f489f3dd1'}, 'artifacts/th14/worker-after-music-after-sixty-oct15/run/checkpoint/runtime-state.json': {'bytes': 14129, 'sha256': '1b3adb3509b53d9092a498b544e0c82cfc8ac4bf8010fe8d37623ea7de1efa6a'}, 'artifacts/th14/worker-after-music-after-sixty-oct15/run/precheckpoint.json': {'bytes': 3241, 'sha256': 'dc95ff87be354bacaf361507af86ce578cdc1aca10cd94749f3b3e7778680725'}, 'artifacts/th14/worker-after-music-after-sixty-oct15/run/receipt.json': {'bytes': 8623, 'sha256': '3817644fe482a9f42f519ca93f3a2c12cd6cca9cc66231bad18deb102b6229d5'}, 'artifacts/th14/worker-after-sixty-main-oct15/checkpoint.py': {'bytes': 7560, 'sha256': '74710d9293c24ca75b19dec03dd1e74f7ee5157073e569c2292f948bbebbb3ef'}, 'artifacts/th14/worker-after-sixty-main-oct15/cooperative_worker.py': {'bytes': 18172, 'sha256': '138a275695d22ca805fdc15114fe3ac7df5b7a6c13c7ee2ec729a8c22ba64e12'}, 'artifacts/th14/worker-after-sixty-main-oct15/plan.json': {'bytes': 6851, 'sha256': 'c5bcea8554cac9c8e09deba5ac9a335b002520223ace6ef17d939a20cdb3059f'}, 'artifacts/th14/worker-after-sixty-main-oct15/resume.py': {'bytes': 30540, 'sha256': '664bbbd01622242013eaaf024c18668b55fb423bf37277a61fc98b8d5aa9a613'}, 'artifacts/th14/worker-after-sixty-main-oct15/run/checkpoint/manifest.json': {'bytes': 180299, 'sha256': '7113826aef67a60c7ff92602e68baa0d91429243cdb9bfedb89aec406eeb11bc'}, 'artifacts/th14/worker-after-sixty-main-oct15/run/checkpoint/runtime-state.json': {'bytes': 18009, 'sha256': '5a523670ab0240a564d004abc0abfad39a52a6dc23cfe1361c5302025c9b5089'}, 'artifacts/th14/worker-after-sixty-main-oct15/run/decoded-0.bin': {'bytes': 362096, 'sha256': '4ed48733ce14f094cef2a9c4f9eb58786ff018b80f3cc70260c72d09413f9607'}, 'artifacts/th14/worker-after-sixty-main-oct15/run/receipt.json': {'bytes': 14704, 'sha256': 'db2b4eb46b8b1ddef8070c0b647d50e73b5dc2896a5d7dfcd386f94f2928a13b'}, 'artifacts/th14/worker-after-stage-enemy-after-sixty-oct15/checkpoint.py': {'bytes': 7675, 'sha256': '12d87f52c64cca17a428c9388c4bb5808a8023ab381c6803f78f0af45a48e840'}, 'artifacts/th14/worker-after-stage-enemy-after-sixty-oct15/cooperative_worker.py': {'bytes': 18172, 'sha256': '138a275695d22ca805fdc15114fe3ac7df5b7a6c13c7ee2ec729a8c22ba64e12'}, 'artifacts/th14/worker-after-stage-enemy-after-sixty-oct15/plan.json': {'bytes': 7145, 'sha256': '64a0fdc8eea039a6fffac45e1099e044fc34762f19a13aa61f502bf760d5755b'}, 'artifacts/th14/worker-after-stage-enemy-after-sixty-oct15/resume.py': {'bytes': 31505, 'sha256': '8cf6558a3340a0445184cb9439e29fbb18ebfac65fd62a553d60dfc061beb753'}, 'artifacts/th14/worker-after-stage-enemy-after-sixty-oct15/run/checkpoint/manifest.json': {'bytes': 267678, 'sha256': '516d7955961ec9971c53105d98aac387877a982401b02e803a2fc3413260843c'}, 'artifacts/th14/worker-after-stage-enemy-after-sixty-oct15/run/checkpoint/runtime-state.json': {'bytes': 62808, 'sha256': 'e9321d1aa044491f8e0f97d92bea7f2317d3c44f9ebdec8c57c7a850bc67ef9a'}, 'artifacts/th14/worker-after-stage-enemy-after-sixty-oct15/run/decoded-0.bin': {'bytes': 6020, 'sha256': 'b17f658e543b48dd09863e5d538d33da22ab77078b12385ef5f26046e6ea4f54'}, 'artifacts/th14/worker-after-stage-enemy-after-sixty-oct15/run/decoded-1.bin': {'bytes': 10064, 'sha256': '83514fe968ed0398e07f71f703c250ba98fd5514ba662765eeb9c1987ea6ed8a'}, 'artifacts/th14/worker-after-stage-enemy-after-sixty-oct15/run/decoded-2.bin': {'bytes': 27956, 'sha256': '37992e7f4d56ff6d744267bdab14615e5f4e8ea355822865b196dca0c5d06372'}, 'artifacts/th14/worker-after-stage-enemy-after-sixty-oct15/run/precheckpoint.json': {'bytes': 3349, 'sha256': 'b916a14281361e4e2c624b4931096bbfd6da2d983705cf4bde0d719867d2b184'}, 'artifacts/th14/worker-after-stage-enemy-after-sixty-oct15/run/receipt.json': {'bytes': 25090, 'sha256': '5fc04d5354db209a6dac2c571b4df1f9c0e288b0800068635b2a6e65cb71d10d'}, 'runtimes/th13/th13_web/artifacts/cpp/engine-th14-build.json': {'bytes': 33491, 'sha256': '75050d7a652d63dd7cc777925848bee85aee018729ad23f0c3aafa3ba21915c1'}, 'tools/th14-staged-loader-production-raw-evidence-check.py': {'bytes': 24206, 'sha256': '5bd3b16dbda27ba2a4fa3487e933768a905efe3755e2281ac6dce7ed278d1141'}}


def read(path):
    path = Path(path)
    if not path.is_absolute(): path = ROOT / path
    path = path.resolve()
    assert path.is_relative_to(ROOT) and not path.is_symlink()
    key = path.relative_to(ROOT).as_posix()
    row = BINDINGS[key]
    raw = path.read_bytes()
    assert len(raw) == row['bytes'] and SHA(raw) == row['sha256'], key
    return raw


def load(path): return json.loads(read(path))


def verify_checkpoint(path):
    m = load(path / 'manifest.json')
    total = 0
    for r in m['regions']:
        p = (path / r['path']).resolve()
        assert p.is_relative_to(path.resolve()) and not p.is_symlink()
        n, digest = 0, hashlib.sha256()
        with p.open('rb') as f:
            while b := f.read(1024 * 1024): n += len(b); digest.update(b)
        assert n == r['bytes'] and digest.hexdigest() == r['sha256']
        total += n
    for r in m['contexts'].values():
        p = (path / r['path']).resolve()
        assert p.is_relative_to(path.resolve()) and not p.is_symlink()
        b = p.read_bytes()
        assert len(b) == r['bytes'] and SHA(b) == r['sha256']
    assert total == m['totalGuestRamBytes'] and m['mainPausedAt'] == 0x469a56
    assert m['workerFiberSlot5'] == 0 and m['ptd'] not in dict(m['heap']['live'])
    stop = m['originalWorkerSummary']['stop']
    assert stop['names'] == ['KERNEL32.dll!ExitThread'] and stop['firstArgument'] == 0
    assert not m['completeGame'] and not m['nativeEquivalent']
    return dict(fullRamBytesRehashed=total, regions=len(m['regions']), bothContextsRehashed=True,
                manifestSha256=SHA(read(path / 'manifest.json')), exitThreadRequestNotServiced=True)


def main():
    assert sys.argv[1:] in ([], ['--write-summary']) and BINDINGS
    for path in BINDINGS: read(path)
    probe = BASE / 'sixty-main-current-core-probe-oct15'
    report = load(probe / 'receipt.json')
    inputs = load(probe / 'native-input-bindings.json')
    build_path = BASE / 'screen-camera-production-build-oct14/build-result.json'
    build_raw = read(build_path); build = json.loads(build_raw)
    assert len(build['sourceHashes']) == 267
    for name, value in build['sourceHashes'].items():
        assert SHA((ROOT / 'runtimes/th12/th12_web' / name).read_bytes()) == value
    objects = {Path(x['path']).resolve(): x['sha256'] for x in build['outputs']}
    names = load(ROOT / 'runtimes/th13/th13_web/artifacts/cpp/engine-th14-build.json')['sources']
    assert len(names) == 141
    for name in names:
        p = BASE / 'screen-camera-production-build-oct14/engine/objects' / (name.replace('/', '_') + '.o')
        assert SHA(p.read_bytes()) == objects[p.resolve()]
    assert report['buildSha256'] == SHA(build_raw)
    assert report['currentGameSourcesBound'] == 267 and report['currentObjectsBound'] == 141
    for p, value in report['fixtureDependencyHashes'].items(): assert SHA(Path(p).read_bytes()) == value
    assert report['fixtureSha256'] == SHA(read(probe / 'fixture.cpp'))
    assert report['toolSha256'] == SHA(read(probe / 'check.mjs'))
    assert report['wasmSha256'] == SHA(read(probe / 'probe.wasm'))
    assert report['nativeInputBindingsSha256'] == SHA(read(probe / 'native-input-bindings.json'))
    for p, value in inputs['bindings'].items(): assert SHA(read(p)) == value

    folders = ['main-during-sixty-wait-oct15'] + [f'main-pumps-{k}-after-sixty-oct15' for k in ('logo', 'background', 'enemy', 'stage-enemy', 'music')]
    rows, native_jobs, main_counts = [], [], []
    for index, folder in enumerate(folders):
        p = BASE / folder; r = load(p / 'receipt.json'); plan = load(p / 'plan.json')
        assert plan['sourceSha256'] == SHA(read(p / 'slice.py'))
        for f, k in [('main_locks.py','lockModelSha256'), ('silent_audio.py','silentAudioModelSha256'),
                     ('checkpoint.py','checkpointHelperSha256'), ('cooperative_worker.py','cooperativeSourceSha256')]:
            assert SHA(read(p / f)) == plan[k]
        assert r['originalMainFrameReturned'] and r['ordinaryMainFrameResumed']
        assert not r['actualAudioPlayed'] and not r['workerResumed']
        if index == 0:
            assert len(r['playerRows']) == 3 and r['workerSixtyMsWaitNotReturned']
            assert r['mainDeclaredElapsedNs'] == 66666600
            assert all(x['replayRng'][2] == 49987 for x in r['playerRows'])
        if 1 <= index <= 4:
            chunks, file = [(2,6),(6,3),(3,10),(16,11)][index-1]
            assert SHA(read(p / 'cpu_textures.py')) == plan['cpuTextureModelSha256']
            assert r['hostExplicitResourceHelperCalls'] == 0 and r['resourceProgress'] == 0
            assert len(r['originalMainResourceCalls']) == chunks
            assert all(c['caller'] == '0x47d799' and not c['hostExplicitHelperCall'] for c in r['originalMainResourceCalls'])
            assert [c['pending'] for c in r['originalMainResourceReturns']] == list(range(2,chunks+1)) + [0]
            base = r['playerRows'][0]['index']; previous = 1; chunk = 0
            for frame in r['frameReturns']:
                if frame['resourceProgress'] != previous:
                    native_jobs.extend([2, file, chunk, base + frame['playerRows']])
                    previous = frame['resourceProgress']; chunk += 1
            assert chunk == chunks
        rows.extend(r['playerRows'])
        main_counts.append(dict(segment=folder, playerCallbacks=len(r['playerRows']),
                                originalFrameCalls=len(r['frameReturns']), codeObservations=r['observations']))
    assert len(rows) == 34 and [x['index'] for x in rows] == list(range(9669,9703))
    assert sum(x['enemyCount'] is None for x in rows) == 11
    assert next(x['index'] for x in rows if x['enemyCount'] is not None) == 9680
    initial = load(BASE / 'worker-after-sixty-main-oct15/run/receipt.json')
    assert initial['mainDeclaredElapsedNsBeforeWake'] == 66666600
    assert [(x['pc'],x['address'],x['bytes'],x['value']) for x in initial['originalGameplayRngStores']] == [
        ('0x45610f','0x4db510',2,62407), ('0x456129','0x4db514',4,0)]
    final = load(BASE / 'worker-after-music-after-sixty-oct15/run/receipt.json')
    assert final['originalCompletionFieldsAtStop'] == [1,0]
    assert [(x['pc'],x['address'],x['value']) for x in final['originalOwnerCompletionWrites']] == [
        ('0x436067','0x4d98fc',0), ('0x436071','0x4d98f8',1)]
    assert final['originalCallbackReturns'][0]['eax'] == 0
    assert final['finalWorkerSlot5'] == 0
    checkpoint = verify_checkpoint(BASE / 'worker-after-music-after-sixty-oct15/run/checkpoint')
    extraction = Path(load(BASE.parent / 'archive-differential/th14.json')['extraction'])
    decoded_bytes, decoded_files = 0, []
    for k in ('sixty-main','logo-after-sixty','background-after-sixty','enemy-after-sixty','stage-enemy-after-sixty'):
        p = BASE / f'worker-after-{k}-oct15'
        r = load(p / 'run/receipt.json')
        plan = load(p / 'plan.json')
        assert SHA(read(p / 'resume.py')) == plan['resumeSourceSha256']
        for d in r['decodedResourceReturns']:
            b = read(p / 'run' / d['filename'])
            assert len(b) == d['bytes'] and SHA(b) == d['sha256']
            assert b == (extraction / d['name']).read_bytes()
            decoded_bytes += len(b); decoded_files.append(d['name'])

    normalizer = ROOT / 'tools/th14-staged-loader-production-raw-evidence-check.py'
    spec = importlib.util.spec_from_file_location('bound_normalizer', normalizer)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    prefix = read(BASE / 'warm-worker-checkpoint-prepared-oct15/run-oct15/original-prefix.jsonl')
    assert SHA(prefix) == 'befb7b0980869fabb6264492f86c3910ad075da662a8086f32fe2b5b4a8b6fad'
    combined = [json.loads(x) for x in prefix.splitlines()] + rows
    assert len(combined) == inputs['totalRows'] == 9703
    expected, available, owners = [], bytearray(), bytearray()
    for i, r in enumerate(combined):
        own = r['enemyCount'] is not None; copy = dict(r)
        if not own: copy['enemyCount'] = 0
        expected.extend(module.normalize(copy)); available.extend([1]*32); owners.append(int(own))
        if not own: available[i*32+25] = 0
    selected = struct.pack('<'+'I'*len(expected),*expected)
    assert selected == read(probe / 'native-selected-state.u32')
    assert bytes(available) == read(probe / 'native-word-availability.u8')
    assert bytes(owners) == read(probe / 'native-owner-presence.u8')
    results = []
    for mode in (0,1):
        raw = read(probe / f'mode-{mode}-selected.u32')
        actual = struct.unpack('<'+'I'*(len(raw)//4),raw)
        actual_owners = read(probe / f'mode-{mode}-owners.u8')
        assert len(actual) == len(expected) and len(actual_owners) == len(owners)
        differences, counts = [], Counter()
        for i in range(9703):
            for j, field in enumerate(module.FIELDS):
                k = i*32+j
                if available[k] and actual[k] != expected[k]:
                    counts[field] += 1
                    differences.append(dict(index=i,field=field,actual=actual[k],expected=expected[k],segment='original-prefix' if i<9669 else 'ordinary-loading'))
            if actual_owners[i] != owners[i]:
                differences.append(dict(index=i,field='enemyOwnerPresent',actual=actual_owners[i],expected=owners[i],segment='original-prefix' if i<9669 else 'ordinary-loading'))
        assert differences == load(probe / f'mode-{mode}-differences.json')
        r = report['reports'][mode]
        assert r['rawDifferenceCount'] == len(differences) and r['callbacks'] == 9703 and not r['error']
        assert r['selectedSha256'] == SHA(raw) and r['ownerPresenceSha256'] == SHA(actual_owners)
        assert all(r['counts'][f] == counts[f] for f in module.FIELDS)
        assert all(counts[f] == 0 for f in module.FIELDS if f not in ('visualSeed','visualCalls'))
        owner_differences = sum(d['field']=='enemyOwnerPresent' for d in differences)
        assert owner_differences == (8 if mode == 0 else 0)
        queue = load(probe / f'mode-{mode}-queue.json')
        assert queue == ([] if mode == 0 else native_jobs)
        assert not r['wholeFrameEquality'] and not report['completeGame'] and not report['nativeEquivalent']
        results.append(dict(realProductionUploadQueue=bool(mode),callbacks=9703,definedRawWordsCompared=sum(available),
                            selectedGameplayWordDifferences=0,ownerPresenceDifferences=owner_differences,
                            visualSeedDifferences=counts['visualSeed'],visualCallCountDifferences=counts['visualCalls'],
                            ordinaryResourceChunks=len(queue)//4,allRawDifferencesRetained=True))
    result = dict(storedEvidenceVerified=True,completeGame=False,nativeEquivalent=False,productionSourcesBound=267,
                  productionObjectsBound=141,ordinaryMainCallbacksDuringInitialSleep=3,ordinarySuffixCallbacks=34,
                  unreadableNativeEnemyCountWords=11,unreadableValuesNeverCompared=True,resourceJobsAtCallbackBoundariesMatched=27,
                  initialGameplayCounterResetByOriginalCode=True,mainSegments=main_counts,results=results,finalCheckpoint=checkpoint,
                  independentlyDecodedBytesCompared=decoded_bytes,independentlyDecodedFiles=decoded_files,
                  bindings=BINDINGS,toolSha256=SHA(Path(__file__).read_bytes()),
                  scope='Stored evidence only. Same intact public Sakuya A Normal replay, current core, ordinary original main resource calls, initial Sleep60 main callbacks, declared cooperative worker services, stopped audio and CPU texture outputs. The production queue arm matches defined selected gameplay words and enemy-owner presence through9703 callbacks; absolute visual RNG differences remain. Eleven count words are unreadable while the Native owner is absent; owner absence is checked independently. Physical concurrent timing, real GPU/audio, complete browser stage transition, remaining modes and whole-game1:1 are not certified.')
    if sys.argv[1:]:
        with OUT.open('x',encoding='utf-8') as f: json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({k:result[k] for k in ('storedEvidenceVerified','ordinarySuffixCallbacks','resourceJobsAtCallbackBoundariesMatched','results','finalCheckpoint')}))


if __name__ == '__main__': main()
