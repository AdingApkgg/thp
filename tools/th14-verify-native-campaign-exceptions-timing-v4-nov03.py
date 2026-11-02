"""Gate TH14 exceptions, Initialize and Scene inputs before raw replay comparison."""
from pathlib import Path
import argparse,subprocess,sys
R=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser(description=__doc__)
for x in ['native','model','exception-output','timing-output','scene-output']:p.add_argument('--'+x,type=Path,required=True)
a,rest=p.parse_known_args();assert '--output' in rest and '--build' in rest
for x in [a.exception_output,a.timing_output,a.scene_output]:assert x.resolve().is_relative_to(R/'artifacts/th14') and not x.exists()
for script,output,needs_model in [('th14-verify-native-debug-exceptions-nov03.py',a.exception_output,False),('th14-verify-native-initialize-timing-v3-nov03.py',a.timing_output,True),('th14-verify-native-scene-boundaries-nov03.py',a.scene_output,True)]:
 cmd=[sys.executable,'-X','utf8',str(R/'tools'/script),'--native',str(a.native)]
 if needs_model:cmd+=['--model',str(a.model)]
 subprocess.run(cmd+['--output',str(output)],cwd=R,check=True)
subprocess.run([sys.executable,'-X','utf8',str(R/'tools/th14-verify-native-campaign.py'),'--native',str(a.native),'--model',str(a.model),*rest],cwd=R,check=True)
