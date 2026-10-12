import {execFileSync} from 'node:child_process';
// The override works when Windows launcher registry discovery is unavailable.
export function nativePython(script,options){
 const executable=process.env.TH_NATIVE_PYTHON;
 return execFileSync(executable||'py',executable?[script]:['-3',script],options);
}
