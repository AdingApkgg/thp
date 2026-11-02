"""Gate debug exceptions and active-stage Initialize coverage before strict TH14 replay verification."""
from pathlib import Path
import argparse,subprocess,sys
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--model',type=Path,required=True);p.add_argument('--exception-output',type=Path,required=True);p.add_argument('--timing-output',type=Path,required=True);a,rest=p.parse_known_args();assert '--output' in rest and '--build' in rest
for x in [a.exception_output,a.timing_output]:assert x.resolve().is_relative_to(R/'artifacts/th14') and not x.exists()
for script,output in [('th14-verify-native-debug-exceptions-nov03.py',a.exception_output),('th14-verify-native-initialize-timing-v3-nov03.py',a.timing_output)]:
 cmd=[sys.executable,'-X','utf8',str(R/'tools'/script),'--native',str(a.native)]
 if script.endswith('v3-nov03.py'):cmd+=['--model',str(a.model)]
 subprocess.run(cmd+['--output',str(output)],cwd=R,check=True)
subprocess.run([sys.executable,'-X','utf8',str(R/'tools/th14-verify-native-campaign.py'),'--native',str(a.native),'--model',str(a.model),*rest],cwd=R,check=True)
