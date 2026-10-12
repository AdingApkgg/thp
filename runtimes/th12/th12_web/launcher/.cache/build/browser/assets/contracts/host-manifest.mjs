import { HOST_PROTOCOL, PRODUCT_GAMES, isGameId, } from "./product-catalog.mjs";
import { RESOURCE_MODE_HOSTED, normalizeResourceMode, } from "./resource-mode.mjs";
export const HOST_MANIFEST_SCHEMA = "eagler-touhou/host-manifest/1";
export const HOST_MANIFEST_FILE = "host-manifest.json";
const SHA256 = /^[a-f0-9]{64}$/i;
const SHA256_VERSION = /^sha256-[a-f0-9]{64}$/i;
function isRecord(value) {
    return value !== null && typeof value === "object" && !Array.isArray(value);
}
function validMusicFileName(value, extension) {
    return typeof value === "string" &&
        new RegExp(`^[A-Za-z0-9][A-Za-z0-9._-]*\\.${extension}$`, "i").test(value);
}
function validMusicFiles(value, extension, allowEmpty) {
    return Array.isArray(value) && (allowEmpty || value.length > 0) &&
        new Set(value).size === value.length && value.every(file => validMusicFileName(file, extension));
}
function validMusicSizes(value, length) {
    return Array.isArray(value) && value.length === length &&
        value.every(size => Number.isSafeInteger(size) && size > 0);
}
function validMidiManifest(value) {
    if (!isRecord(value) || !validMusicFiles(value.files, "mid", true))
        return false;
    return value.sizes == null || validMusicSizes(value.sizes, value.files.length);
}
function validOggManifest(value) {
    if (value == null)
        return true;
    if (!isRecord(value))
        return false;
    const files = value.files;
    const sizes = value.sizes;
    const sha256 = value.sha256;
    return typeof value.version === "string" && SHA256_VERSION.test(value.version) &&
        validMusicFiles(files, "ogg", false) && validMusicSizes(sizes, files.length) &&
        Array.isArray(sha256) && files.length === sha256.length &&
        sha256.every(hash => typeof hash === "string" && SHA256.test(hash));
}
function validOfflineCompatibility(item, resourceMode) {
    if (resourceMode === RESOURCE_MODE_HOSTED)
        return true;
    const compatibility = item.offlineCompatibility;
    const gameData = item.gameData;
    if (!isRecord(compatibility) || !isRecord(gameData))
        return false;
    const runtimeCompatibility = compatibility.runtimeCompatibility;
    const languages = compatibility.languages;
    const requiredShared = compatibility.requiredShared;
    return isRecord(runtimeCompatibility) && isRecord(languages) &&
        compatibility.schema === "eagler-touhou/offline-game-pack/1" &&
        runtimeCompatibility.protocol === HOST_PROTOCOL &&
        runtimeCompatibility.dataLayout === gameData.layout &&
        runtimeCompatibility.versionSource === "offline-pack" &&
        Array.isArray(requiredShared) &&
        ["/msgothic.ttc", "/unifont.otf"].every(target => requiredShared.includes(target)) &&
        languages.source === "offline-pack" &&
        Array.isArray(languages.baseline) && languages.baseline.includes("ja");
}
function validHostRuntimeFeatures(value) {
    if (value == null)
        return true;
    if (!isRecord(value))
        return false;
    const allowed = new Set(["thprac", "focusHitbox"]);
    return Object.entries(value).every(([key, item]) => allowed.has(key) && typeof item === "boolean");
}
function validGame(gameId, value, resourceMode) {
    if (!isGameId(gameId) || !isRecord(value) || typeof value.runtime !== "string" || !value.runtime)
        return false;
    const music = value.music;
    const gameData = value.gameData;
    if (!isRecord(music) || !validMidiManifest(music.midi) || !isRecord(gameData))
        return false;
    const product = PRODUCT_GAMES[gameId];
    if ("multiplayerRuntime" in product &&
        (typeof value.multiplayerRuntime !== "string" || !value.multiplayerRuntime))
        return false;
    const expectedDataPath = product.package.dataTarget.slice(1);
    return typeof gameData.version === "string" && SHA256_VERSION.test(gameData.version) &&
        typeof gameData.layout === "string" && SHA256_VERSION.test(gameData.layout) &&
        gameData.path === expectedDataPath &&
        Number.isSafeInteger(gameData.bytes) && Number(gameData.bytes) > 0 &&
        typeof gameData.sha256 === "string" && SHA256.test(gameData.sha256) &&
        validHostRuntimeFeatures(value.features) && validOggManifest(music.ogg) &&
        validOfflineCompatibility(value, resourceMode);
}
function validOptionalUrl(value, protocols) {
    if (value == null)
        return true;
    if (typeof value !== "string" || !value)
        return false;
    try {
        return protocols.has(new URL(value).protocol);
    }
    catch {
        return false;
    }
}
function validOriginMigration(value) {
    return value == null || (isRecord(value) && value.mode === "http-to-https");
}
export function hostOriginMigrationAvailable(manifest, protocol) {
    return protocol === "https:" && manifest.shared.originMigration?.mode === "http-to-https";
}
export function validateHostManifest(value) {
    if (!isRecord(value) || value.schema !== HOST_MANIFEST_SCHEMA || value.protocol !== HOST_PROTOCOL ||
        typeof value.profile !== "string" || !value.profile || !isRecord(value.shared) || !isRecord(value.games)) {
        throw new Error("invalid Host Manifest");
    }
    const resourceMode = normalizeResourceMode(value.shared.resourceMode);
    if (!resourceMode)
        throw new Error("invalid Host Manifest resource mode");
    if (resourceMode === RESOURCE_MODE_HOSTED &&
        (typeof value.shared.vanillaFont !== "string" || typeof value.shared.unicodeFont !== "string")) {
        throw new Error("hosted Host Manifest is missing shared fonts");
    }
    if (resourceMode !== RESOURCE_MODE_HOSTED &&
        (value.shared.vanillaFont != null || value.shared.unicodeFont != null)) {
        throw new Error("import Host Manifest must not publish shared font URLs");
    }
    const fallback = value.shared.gameDataFallback;
    if (fallback != null && (!isRecord(fallback) || typeof fallback.url !== "string" ||
        !validOptionalUrl(fallback.url, new Set(["https:"])) ||
        (fallback.hint != null && typeof fallback.hint !== "string"))) {
        throw new Error("invalid Host Manifest gameDataFallback");
    }
    if (!validOptionalUrl(value.shared.netplayRelay, new Set(["ws:", "wss:"]))) {
        throw new Error("invalid Host Manifest netplayRelay");
    }
    if (!validOriginMigration(value.shared.originMigration)) {
        throw new Error("invalid Host Manifest originMigration");
    }
    const games = value.games;
    const actualGames = Object.keys(games).sort();
    if (!actualGames.length || actualGames.some(game => !isGameId(game)) ||
        actualGames.some(game => !validGame(game, games[game], resourceMode))) {
        throw new Error("invalid Host Manifest games");
    }
    return {
        ...value,
        schema: HOST_MANIFEST_SCHEMA,
        protocol: HOST_PROTOCOL,
        profile: value.profile,
        shared: { ...value.shared, resourceMode },
        games: games,
    };
}
