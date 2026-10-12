export const multiplayerShareSettingsStorageKey = (product) => `eagler-touhou-${product}-share-singleplayer-settings-v1`;
export const multiplayerLoadoutStorageKey = (product) => `eagler-touhou-${product}-loadout-v1`;
function browserLocalStorage() {
    try {
        return globalThis.localStorage;
    }
    catch {
        return null;
    }
}
export function normalizePreferredLoadout(value, maxLoadout) {
    const parsed = Number(value);
    return Number.isInteger(parsed) && parsed >= 0 && parsed < Math.max(0, Math.trunc(maxLoadout)) ? parsed : 0;
}
export function createMultiplayerPreferenceStore({ storage = browserLocalStorage(), } = {}) {
    const load = ({ product, multiplayer, maxLoadout }) => {
        if (!multiplayer)
            return { shareSingleplayerSettings: true, preferredLoadout: null };
        let shareSingleplayerSettings = true;
        let savedLoadout = null;
        try {
            shareSingleplayerSettings = storage?.getItem(multiplayerShareSettingsStorageKey(product)) !== "0";
        }
        catch {
            shareSingleplayerSettings = true;
        }
        try {
            savedLoadout = storage?.getItem(multiplayerLoadoutStorageKey(product));
        }
        catch { }
        return {
            shareSingleplayerSettings,
            preferredLoadout: normalizePreferredLoadout(savedLoadout, maxLoadout),
        };
    };
    const persistShareSingleplayerSettings = (product, enabled) => {
        try {
            storage?.setItem(multiplayerShareSettingsStorageKey(product), enabled ? "1" : "0");
        }
        catch { }
    };
    const persistPreferredLoadout = (product, loadout) => {
        if (!Number.isInteger(loadout) || loadout < 0)
            return;
        try {
            storage?.setItem(multiplayerLoadoutStorageKey(product), String(loadout));
        }
        catch { }
    };
    return Object.freeze({ load, persistShareSingleplayerSettings, persistPreferredLoadout });
}
