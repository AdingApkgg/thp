// Exercise actual Launcher bootstrap snippets and App Shell client at the
// real top-level-await boundary, without editing frozen packages or a browser.
import assert from 'node:assert/strict';
import {readFileSync, writeFileSync, existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {stripTypeScriptTypes} from 'node:module';
import {createHash} from 'node:crypto';
import {runInNewContext} from 'node:vm';

const root = resolve(import.meta.dirname, '..');
const launcher = resolve(root, 'runtimes/th12/th12_web/launcher');
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const appPath = resolve(launcher, 'src/launcher/app.mts');
const clientPath = resolve(launcher, 'src/launcher/app-shell-client.mts');
const source = readFileSync(appPath, 'utf8'), clientSource = readFileSync(clientPath, 'utf8');
const compile = text => stripTypeScriptTypes(text, {mode:'strip'});
const factoryModule = await import('data:text/javascript;base64,' + Buffer.from(compile(clientSource)).toString('base64'));
const baselineReportPath = resolve(root, 'docs/porting/th14-launcher-preview-prepared-staged-capture-oct14.json');
const baselineReport = JSON.parse(readFileSync(baselineReportPath)); assert.equal(baselineReport.passed, true);
const baselinePath = resolve(baselineReport.site, 'assets/launcher/app.mjs');
const baseline = readFileSync(baselinePath, 'utf8');
assert.equal(sha(Buffer.from(baseline)), baselineReport.files['assets/launcher/app.mjs'].sha256);

let assertions = 0;
const test = (actual, expected) => {assert.deepEqual(actual, expected); ++assertions;};
function boot(text, label) {
  // These are actual top-level declarations. Balance their existing bodies,
  // including quoted strings/comments, rather than rewriting their contents.
  function bracedEnd(start) {
    let depth = 0, quote = '', line = false, block = false;
    for (let i = text.indexOf('{', start); i < text.length; ++i) {
      const c = text[i], next = text[i + 1];
      if (line) {if (c === '\n') line = false; continue;}
      if (block) {if (c === '*' && next === '/') {block = false; ++i;} continue;}
      if (quote) {if (c === '\\') ++i; else if (c === quote) quote = ''; continue;}
      if (c === '/' && next === '/') {line = true; ++i; continue;}
      if (c === '/' && next === '*') {block = true; ++i; continue;}
      if (c === '"' || c === "'" || c === '`') {quote = c; continue;}
      if (c === '{') ++depth;
      else if (c === '}' && --depth === 0) return i + 1;
    }
    throw Error('Unclosed source body in ' + label);
  }
  function namedVariable(name) {
    const match = new RegExp('^(?:let|const) ' + name + '(?=\\s|:)', 'm').exec(text); assert(match, name);
    const at = match.index, end = name === 'state' ? bracedEnd(at) : at;
    return {at, text:text.slice(at, text.indexOf(';', end) + 1)};
  }
  const state = namedVariable('state');
  const assignment = /^appShellClient = createAppShellClient\(/m.exec(text);
  const declaration = /^function renderServerStatusNote\(/m.exec(text);
  const firstAwait = /^await\b/m.exec(text); assert(assignment && declaration && firstAwait);
  const creation = {at:assignment.index, text:text.slice(assignment.index, text.indexOf(';', bracedEnd(assignment.index)) + 1)};
  const status = {at:declaration.index, text:text.slice(declaration.index, bracedEnd(declaration.index))};
  const nodes = ['appShellClient', 'serverUpdateState', 'serverConfigurationWarning', 'remoteCatalogError']
    .map(namedVariable); assert(nodes.every(Boolean));
  const parts = [...nodes, state, creation, status].map(node => ({at:node.at,
    text:node.text + (node === state ? '\ncaptureLauncherState(state);' : '')}));
  // The omitted migration operation is held at its actual source position.
  // No state/render/registration logic is replaced by a test implementation.
  parts.push({at:firstAwait.index, text:'await initializationGate;'});
  parts.sort((a, b) => a.at - b.at);
  return {code:compile('(async () => {\n' + parts.map(p => p.text).join('\n') + '\n})()'),
    stateText:state.text, creationText:creation.text, statusText:status.text,
    stateBeforeClient:state.at < creation.at,
    stateBeforeAwait:state.at < firstAwait.index};
}
const previous = boot(baseline, 'frozen-app.mjs'), current = boot(source, 'app.mts');
test(previous.stateBeforeClient, false); test(previous.stateBeforeAwait, false);
test(current.stateBeforeClient, true); test(current.stateBeforeAwait, true);
const normalized = text => compile(text).replace(/\s+/g, '');
test(normalized(current.stateText), normalized(previous.stateText));
test(normalized(current.creationText), normalized(previous.creationText));
test(normalized(current.statusText), normalized(previous.statusText));

// Reconstruct the complete prior actual source, proving that the only source
// edit is the unchanged state constructor relocation and two explanatory lines.
const nl = source.includes('\r\n') ? '\r\n' : '\n';
const comment = '// App Shell notifications may run while top-level package migration awaits.' + nl +
  '// Initialize their Launcher state before starting registration.' + nl;
const priorSource = source.replace(comment + current.stateText + nl + nl, '')
  .replace('const productIds ', current.stateText + nl + 'const productIds ');
test(sha(Buffer.from(priorSource)), '423a534a57c5d051c906bd3c7ff56a28595f5e3c60e5ee38c58bbe1917ce376b');

async function pausedBootstrap(program, {waiting = false, updateFails = false} = {}) {
  const events = new Map(), workerEvents = new Map(), scheduled = [], warnings = [];
  let client, launcherState, resume;
  const gate = new Promise(accept => {resume = accept;});
  const worker = {state:'installing', addEventListener(name, callback){workerEvents.set(name, callback);}};
  const registration = {waiting:waiting ? {} : null, installing:worker,
    addEventListener(name, callback){events.set(name, callback);},
    async update(){if (updateFails) throw new Error('Declared update failure');}};
  const serviceWorker = {controller:{}, async register(){return registration;}, async getRegistration(){return registration;}};
  const note = {hidden:false, textContent:'', dataset:{}, removeAttribute(name){if (name === 'data-kind') delete this.dataset.kind;}};
  const sandbox = {initializationGate:gate, defaultOptions:{},
    captureLauncherState(value){launcherState = value;},
    document:{getElementById:id => id === 'serverStatusNote' ? note : null, querySelector:() => null},
    t:key => key, remoteFailureReason:() => 'Declared update failure',
    createAppShellClient(options){
      client = factoryModule.createAppShellClient({...options, serviceWorker, secureContext:true,
        schedule:callback => scheduled.push(callback), reload:() => {},
        logger:{warn(message, error){warnings.push({message, error:String(error)});}}});
      return client;
    }};
  const evaluation = runInNewContext(program.code, sandbox, {timeout:1000});
  let readyError;
  try {await client.ready;} catch (error) {readyError = error;}
  await Promise.resolve();
  return {client, note, scheduled, warnings, readyError, state:() => launcherState,
    installed(){events.get('updatefound')(); worker.state = 'installed'; workerEvents.get('statechange')();},
    activated(){worker.state = 'activated'; workerEvents.get('statechange')();},
    async finish(){resume(); await evaluation;}};
}

const old = await pausedBootstrap(previous);
let observedError;
try {old.installed();} catch (error) {observedError = error;}
assert(observedError && observedError.name === 'ReferenceError' && /state.*initialization/.test(observedError.message)); ++assertions;
test(old.state(), undefined); await old.finish();
const retainedFailure = {name:observedError.name, message:observedError.message,
  trigger:'Actual frozen App Shell updatefound/installed callback while migration await is unresolved',
  appSha256:sha(Buffer.from(baseline))};

const replacement = await pausedBootstrap(current);
test(replacement.readyError, undefined); test(replacement.state().launched, false);
replacement.installed(); test(replacement.note.dataset.kind, 'update');
test(replacement.note.textContent, 'status.applyingSiteUpdate');
replacement.state().launched = true; replacement.activated();
test(replacement.note.textContent, 'status.siteUpdateAfterExit'); test(replacement.scheduled.length, 0);
replacement.state().launched = false;
test(replacement.client.maybeReload(), true); test(replacement.scheduled.length, 1);
test(replacement.client.maybeReload(), false); await replacement.finish();

const waiting = await pausedBootstrap(current, {waiting:true});
test(waiting.readyError, undefined); test(waiting.note.textContent, 'status.applyingSiteUpdate'); await waiting.finish();
const failure = await pausedBootstrap(current, {updateFails:true});
test(failure.client.snapshot().updateCheckFailed, true);
test(failure.note.dataset.kind, 'offline'); test(failure.note.textContent, 'status.updateCheckFailed');
test(failure.warnings.length, 1); test(failure.warnings[0].message, 'App Shell update check unavailable'); await failure.finish();

const receipt = {launcherStateInitializationVerified:true, productionGameChanged:false,
  frozenPackagesChanged:false, appShellNotificationsPreserved:true, appShellRegistrationLogicChanged:false,
  loggerSuppression:false, quietAudioChanged:false, browserExecuted:false, assertions,
  actualSource:{path:appPath, beforeSha256:sha(Buffer.from(priorSource)), sha256:sha(Buffer.from(source)),
    onlyUnchangedStateRelocationAndTwoComments:true},
  clientSource:{path:clientPath, sha256:sha(Buffer.from(clientSource))},
  baseline:{report:baselineReportPath, reportSha256:sha(readFileSync(baselineReportPath)),
    app:baselinePath, appSha256:sha(Buffer.from(baseline))},
  retainedFailure, cases:['installed callback during migration await', 'already waiting registration',
    'running game defers reload until exit', 'update failure remains visible and logged'],
  toolSha256:sha(readFileSync(import.meta.filename)), typeStrippingRuntime:process.version,
  retainedSetupFailure:'First unit setup attempted the unavailable classic TypeScript API from the local TypeScript7 package; MODULE_NOT_FOUND occurred before any regression case or receipt. The unit now uses built-in Node type erasure.',
  requiresFreshLauncherPackage:true,
  scope:'Actual source bootstrap/state/render snippets are executed in their original order around the real first top-level-await position, using the actual unmodified App Shell client and declared Service Worker/DOM/scheduler dependencies. Frozen module reproduces TDZ; corrected source retains notices, reload deferral and warning delivery. No browser, service, game build, audio hook or frozen package is modified or verified by this unit.'};
const output = resolve(root, 'docs/porting/th14-launcher-state-initialization-verified-oct14.json');
assert(!existsSync(output), 'New receipt only');
writeFileSync(output, JSON.stringify(receipt, null, 2) + '\n', {flag:'wx'});
console.log(JSON.stringify({launcherStateInitializationVerified:true, assertions,
  actualSourceSha256:receipt.actualSource.sha256, beforeFailure:retainedFailure,
  report:output, reportSha256:sha(readFileSync(output)), toolSha256:receipt.toolSha256,
  requiresFreshLauncherPackage:true}, null, 2));
