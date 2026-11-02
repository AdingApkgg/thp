"""Run TH14 original-event timing checks before the existing strict campaign gate."""
from pathlib import Path
import argparse,subprocess,sys
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--model',type=Path,required=True);p.add_argument('--timing-output',type=Path,required=True);a,rest=p.parse_known_args()
assert '--output' in rest and '--build' in rest,'The strict campaign output and build are required'
assert a.timing_output.resolve().is_relative_to(R/'artifacts/th14') and not a.timing_output.exists()
subprocess.run([sys.executable,'-X','utf8',str(R/'tools/th14-verify-native-initialize-timing-v2-nov03.py'),'--native',str(a.native),'--model',str(a.model),'--output',str(a.timing_output)],cwd=R,check=True)
subprocess.run([sys.executable,'-X','utf8',str(R/'tools/th14-verify-native-campaign.py'),'--native',str(a.native),'--model',str(a.model),*rest],cwd=R,check=True)
