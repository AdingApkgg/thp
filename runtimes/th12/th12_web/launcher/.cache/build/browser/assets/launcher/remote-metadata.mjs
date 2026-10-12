import { HOST_MANIFEST_FILE, validateHostManifest } from "../contracts/host-manifest.mjs";
import { RELEASE_CATALOG_FILE, validateReleaseCatalog } from "../contracts/release-catalog.mjs";
async function settle(load) {
    try {
        return Object.freeze({ ok: true, value: await load() });
    }
    catch (error) {
        return Object.freeze({ ok: false, error });
    }
}
export async function loadRemoteMetadata(fetchJson) {
    if (typeof fetchJson !== "function")
        throw new TypeError("fetchJson must be a function");
    const [releaseCatalog, hostManifest] = await Promise.all([
        settle(async () => validateReleaseCatalog(await fetchJson(RELEASE_CATALOG_FILE, "release-catalog"))),
        settle(async () => validateHostManifest(await fetchJson(HOST_MANIFEST_FILE, "host-manifest"))),
    ]);
    return Object.freeze({ releaseCatalog, hostManifest });
}
