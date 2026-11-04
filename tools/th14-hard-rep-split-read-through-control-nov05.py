"""Disable only the two inferred REP read waits; retain the failing control."""
from pathlib import Path
import argparse, hashlib, json, subprocess, time

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/reimub-hard-full-context-nov05/retry1'
SHA = lambda raw: hashlib.sha256(raw).hexdigest()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); out = a.output.resolve()
    assert out.is_relative_to(R / 'artifacts/th14') and not out.exists()
    source = R / 'tools/th14-compare-native-hard-rep-split-v4-nov05.mjs'
    raw = source.read_bytes()
    assert SHA(raw) == '1af7e21434fa1245980cbe7d020d238344dba213d4e99afef9b111280d104a61'
    text = raw.decode()
    begin = "    assert.equal(c.observed_perspective_rep_split(split.stage,callback,split.ordinal,split.pause,split.start,split.end,baseNow+BigInt(firstNs)-playerOrigin,baseNow+BigInt(lastNs)-playerOrigin),1);"
    end = "    perspectiveRepSplits.push({...split,firstNs,lastNs,changedNativeWords,nativeReadGenerationClassificationUsed:true,readerPausePrefixObserved:true,publisherInterleavingInferred:true,exactOriginalScheduleRecovered:false});continue;"
    assert text.count(begin) == text.count(end) == 1
    text = text.replace(begin, '    // Negative control: no split clock/read wait registered.')
    text = text.replace(end, '    continue; // Keep the same remaining scheduler inputs.')
    out.mkdir(parents=True)
    # Relative imports of the original driver resolve from tools, so use a
    # retained copy there with a unique, explicitly diagnostic filename.
    driver = R / 'tools/th14-hard-rep-read-through-control-generated-nov05.mjs'
    assert not driver.exists(); driver.write_bytes(text.encode())
    argv = json.loads((H / 'full/current-core-comparison-v4/argv.json').read_bytes())
    argv[2] = str(driver); argv[argv.index('--output') + 1] = str(out / 'model')
    plan = dict(argv=argv, parentDriverSha256=SHA(raw), controlDriverSha256=SHA(driver.read_bytes()),
                disabledOnlyInferredPerspectiveRepReadWaits=True, expectedToFail=True,
                independentTimingAccepted=False, completeGame=False)
    (out / 'plan.json').write_text(json.dumps(plan, indent=2) + '\n')
    started = time.monotonic()
    with (out / 'process.log').open('wb') as log:
        result = subprocess.run(argv, cwd=R, stdout=log, stderr=subprocess.STDOUT,
                                timeout=180, creationflags=subprocess.CREATE_NO_WINDOW)
    end = dict(exitCode=result.returncode, elapsedSeconds=time.monotonic() - started,
               expectedFailureRetained=result.returncode != 0, completeGame=False)
    (out / 'process-end.json').write_text(json.dumps(end, indent=2) + '\n')
    print(json.dumps(end))
    assert result.returncode != 0, 'The negative control unexpectedly passed'

if __name__ == '__main__': main()
