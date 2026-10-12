// The reference assets a suite needs are the ORIGINALS, and the originals live in the machine's game
// installs, not in the repository. Round 306's census found 31 of 142 suites failing before they ran,
// on three hard-coded paths: the th11 data file sixteen times and the D3DX9 reference DLL fourteen
// times. A test that cannot find its input has not tested anything, so the lookup is one function.
//
// Search order, most explicit first:
//   1. TH_ORIGINALS, TH_ORIGINALS_DIR - an environment that says where they are;
//   2. the runtime's own reference tree (runtimes/th12/th12_web/reference) for derived assets;
//   3. the runtime's parent directory, including the `[th11] 东方地灵殿 ...` copy convention;
//   4. the game installs, TH_GAMES or H:/Games/th/<title>/ (th11 .. th20);
//   5. the system directories, for the DirectX redists the games link against.
// A miss throws with the whole search behind it, because "ENOENT on a path I have never seen" is how
// this round started.
import {existsSync,readdirSync} from 'node:fs';
import {basename,join,resolve} from 'node:path';
import {root} from './helpers.mjs';

const TITLES=['th11','th12','th13','th14','th15','th16','th17','th18','th19','th20'];

function searchRoots(){
  const roots=[];
  for(const key of ['TH_ORIGINALS','TH_ORIGINALS_DIR'])
    if(process.env[key])roots.push(resolve(process.env[key]));
  roots.push(resolve(root,'reference'));
  roots.push(resolve(root,'..'));
  for(const base of installRoots())roots.push(base);
  roots.push('C:/Windows/SysWOW64','C:/Windows/System32');
  return roots;
}

// The installs on this machine are numbered directories (H:\Games\th\11), while the titles are named
// th11; both spellings are searched, because a reference that resolves on one machine and not another
// is the failure this module exists to remove.
function installRoots(){
  const gamesDir=process.env.TH_GAMES||'H:/Games/th';
  const roots=[];
  for(const title of TITLES){
    roots.push(join(gamesDir,title));
    roots.push(join(gamesDir,title.slice(2)));
  }
  return roots;
}

export function original(name){
  const searched=[];
  const bases=[resolve(root,'..'),...installRoots()];
  for(const base of bases){
    if(!existsSync(base))continue;
    for(const entry of readdirSync(base)){
      // the localized copies are directories named `[th11] ...`; a suite written before this helper
      // resolved into one of them, so the helper looks there too
      if(entry.startsWith('[')&&entry.includes(basename(name).slice(0,4))){
        const candidate=join(base,entry,name);
        searched.push(candidate);
        if(existsSync(candidate))return candidate;
      }
    }
  }
  for(const base of searchRoots()){
    const candidate=join(base,name);
    searched.push(candidate);
    if(existsSync(candidate))return candidate;
    // a nested request (native/d3dx9_37.dll) may be satisfied by the system directory's basename
    const flat=join(base,basename(name));
    if(flat!==candidate){searched.push(flat);if(existsSync(flat))return flat;}
  }
  throw new Error(`original asset not found: ${name}\n  searched:\n    ${searched.join('\n    ')}`);
}

export function hasOriginal(name){
  try{original(name);return true;}catch{return false;}
}
