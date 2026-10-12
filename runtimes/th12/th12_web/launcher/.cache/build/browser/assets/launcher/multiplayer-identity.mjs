export const multiplayerDisplayNameStorageKey = "eagler-touhou-mp-display-name-v1";
export const multiplayerDisplayNameLockedStorageKey = "eagler-touhou-mp-display-name-locked-v1";
export const multiplayerLobbyClientStorageKey = (product) => `eagler-touhou-${product}-lobby-client-v1`;
export function normalizeMultiplayerDisplayName(value) {
    return [...String(value || "").replace(/[\u0000-\u001f\u007f]/g, "").trim()].slice(0, 12).join("");
}
export function multiplayerDisplayInitial(name, fallback = "观") {
    return [...normalizeMultiplayerDisplayName(name)][0] || fallback;
}
export function validMultiplayerClientId(value) {
    return typeof value === "string" && /^[A-Za-z0-9_-]{8,64}$/.test(value);
}
function browserStorage(name) {
    try {
        return globalThis[name];
    }
    catch {
        return null;
    }
}
export function createMultiplayerIdentityStore({ persistentStorage = browserStorage("localStorage"), sessionStorage = browserStorage("sessionStorage"), randomWords = () => {
    const words = new Uint32Array(2);
    globalThis.crypto.getRandomValues(words);
    return [words[0], words[1]];
}, fallbackClientId = () => `c${Math.random().toString(36).slice(2)}${Date.now().toString(36)}`, } = {}) {
    const displayNameLocked = (fallbackName = "") => {
        if (!persistentStorage)
            return !!normalizeMultiplayerDisplayName(fallbackName);
        try {
            return persistentStorage.getItem(multiplayerDisplayNameLockedStorageKey) === "1" &&
                !!normalizeMultiplayerDisplayName(persistentStorage.getItem(multiplayerDisplayNameStorageKey) || "");
        }
        catch {
            return !!normalizeMultiplayerDisplayName(fallbackName);
        }
    };
    const loadDisplayName = () => {
        if (!persistentStorage)
            return "";
        try {
            const name = normalizeMultiplayerDisplayName(persistentStorage.getItem(multiplayerDisplayNameStorageKey) || "");
            if (name)
                persistentStorage.setItem(multiplayerDisplayNameLockedStorageKey, "1");
            return name;
        }
        catch {
            return "";
        }
    };
    const storeDisplayNameOnce = (value, fallbackName = "") => {
        const name = normalizeMultiplayerDisplayName(value);
        if (!name || displayNameLocked(fallbackName))
            return { stored: false, name };
        try {
            persistentStorage?.setItem(multiplayerDisplayNameStorageKey, name);
            persistentStorage?.setItem(multiplayerDisplayNameLockedStorageKey, "1");
        }
        catch { }
        return { stored: true, name };
    };
    const lobbyClientId = (product) => {
        const key = multiplayerLobbyClientStorageKey(product);
        try {
            const existing = sessionStorage?.getItem(key) || "";
            if (validMultiplayerClientId(existing))
                return existing;
            const [first, second] = randomWords();
            const value = `c${first.toString(36).padStart(7, "0")}${second.toString(36).padStart(7, "0")}`;
            sessionStorage?.setItem(key, value);
            return value;
        }
        catch {
            return fallbackClientId();
        }
    };
    return Object.freeze({ displayNameLocked, loadDisplayName, storeDisplayNameOnce, lobbyClientId });
}
