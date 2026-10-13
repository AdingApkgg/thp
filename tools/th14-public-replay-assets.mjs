// Keep a public player's original replay intact; attest the private demo entry
// replacement using the existing archive roundtrip. No playback success claim.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),sha=b=>createHash('sha256').update(b).digest('hex');
const path=resolve(root,process.argv[2]),metadataPath=resolve(path,'../th14_udzp05-source.json');
const data=readFileSync(path),metadata=JSON.parse(readFileSync(metadataPath));
assert.equal(sha(data),metadata.sha256);assert.equal(metadata.status,'PARSED_NOT_PLAYBACK_VERIFIED');
await import('./th14-native-campaign-assets.mjs');
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'))),original=readFileSync(target.dataArchives['th14.dat'].path);
const manifestPath=resolve(root,'artifacts/th14/native-campaign-assets',sha(original).slice(0,12)+'-'+sha(data).slice(0,12),'manifest.json');
const report=JSON.parse(readFileSync(manifestPath));
assert.equal(report.replaySha256,metadata.sha256);assert.equal(report.unchangedEntries,226);
report.publicRecordingSource=metadata;report.publicRecordingSourceMetadataSha256=sha(readFileSync(metadataPath));
report.publicRecordingAssetWrapperSha256=sha(readFileSync(import.meta.filename));
report.scope='Private diagnostic archive with one demo0 entry replaced by the intact public player recording, including its original suffix. Every other ordinal entry and its ordering remain byte-identical after archive roundtrip. Public source/version/header claims are input provenance only, not native playback, completion or equivalence certification.';
writeFileSync(manifestPath,JSON.stringify(report,null,2)+'\n');
