"""Run the TH14 debug-exception, original-event timing and existing replay gates."""
from pathlib import Path
import argparse,subprocess,sys
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--model',type=Path,required=True);p.add_argument('--exception-output',type=Path,required=True);p.add_argument('--timing-output',type=Path,required=True);a,rest=p.parse_known_args()
assert '--output' in rest and '--build' in rest
assert a.exception_output.resolve().is_relative_to(R/'artifacts/th14') and not a.exception_output.exists()
subprocess.run([sys.executable,'-X','utf8',str(R/'tools/th14-verify-native-debug-exceptions-nov03.py'),'--native',str(a.native),'--output',str(a.exception_output)],cwd=R,check=True)
subprocess.run([sys.executable,'-X','utf8',str(R/'tools/th14-verify-native-campaign-with-timing-nov03.py'),'--native',str(a.native),'--model',str(a.model),'--timing-output',str(a.timing_output),*rest],cwd=R,check=True)
