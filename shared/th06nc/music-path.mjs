// Native7bcf4..7bd7e redirects only the original data/bgm/ prefix, after
// MUSC unlock processing. Explicit bgm2 paths and other inputs survive.
export function resolveMusicPath(path,soundtrack=0){return soundtrack===1&&path.startsWith('data/bgm/')?'data/bgm2/'+path.slice(9):path;}
