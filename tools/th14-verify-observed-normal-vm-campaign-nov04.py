"""Gate exceptions, Initialize, witnessed VM/Scene inputs and independent raw fields."""
from pathlib import Path
import argparse, subprocess, sys
R=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser(description=__doc__)
for name in ['native','model','build','normal-vm-inputs','exception-output','timing-output','scene-output','output']:p.add_argument('--'+name,type=Path,required=True)
p.add_argument('--prefix',type=int,required=True);a=p.parse_args();assert a.prefix==35000
for path in(a.exception_output,a.timing_output,a.scene_output,a.output):assert path.resolve().is_relative_to(R/'artifacts/th14')and not path.exists()
commands=[
    ['th14-verify-native-debug-exceptions-nov03.py','--native',str(a.native),'--output',str(a.exception_output)],
    ['th14-verify-native-initialize-timing-v3-nov03.py','--native',str(a.native),'--model',str(a.model),'--output',str(a.timing_output)],
    ['th14-verify-observed-normal-vm-scene-nov04.py','--native',str(a.native),'--model',str(a.model),'--build',str(a.build),'--normal-vm-inputs',str(a.normal_vm_inputs),'--output',str(a.scene_output)],
    ['th14-verify-native-campaign.py','--native',str(a.native),'--model',str(a.model),'--build',str(a.build),'--prefix',str(a.prefix),'--output',str(a.output)]
]
for command in commands:subprocess.run([sys.executable,'-X','utf8',str(R/'tools'/command[0]),*command[1:]],cwd=R,check=True)
