from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
s=(ROOT/'tools/th14-gpu-original-shapes.html').read_text(encoding='utf8')
s=s.replace("import create from './gpu.mjs';","const variant=new URL(location.href).searchParams.get('variant')||'clip-linear';\nconst {default:create}=await import('./'+variant+'/gpu.mjs');")
s=s.replace("fetch('./build.json')","fetch('./'+variant+'/build.json')")
s=s.replace('const report={completeGame:false','const report={diagnosticOnly:true,variant,completeGame:false')
(ROOT/'tools/th14-gpu-original-shapes-variants.html').write_text(s,encoding='utf8')
print('Prepared candidate selection page')
