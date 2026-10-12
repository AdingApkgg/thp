export const multiplayerSpectatorRailPositionStorageKey = "eagler-touhou-mp-spectator-rail-position-v1";
export const multiplayerSpectatorRailLegacyPositionStorageKey = "eagler.mpSpectatorRail.mobilePosition.v1";
function browserLocalStorage() {
    try {
        return globalThis.localStorage;
    }
    catch {
        return null;
    }
}
function parsePosition(raw) {
    if (raw == null)
        return null;
    try {
        const value = JSON.parse(raw);
        if (!value || !Number.isFinite(value.x) || !Number.isFinite(value.y))
            return null;
        return { x: value.x, y: value.y };
    }
    catch {
        return null;
    }
}
export function createMultiplayerSpectatorRailPositionStore({ storage = browserLocalStorage(), } = {}) {
    const load = () => {
        if (!storage)
            return null;
        let raw = null;
        try {
            raw = storage.getItem(multiplayerSpectatorRailPositionStorageKey);
        }
        catch {
            return null;
        }
        if (raw == null) {
            let legacy = null;
            try {
                legacy = storage.getItem(multiplayerSpectatorRailLegacyPositionStorageKey);
            }
            catch {
                return null;
            }
            if (legacy != null) {
                try {
                    storage.setItem(multiplayerSpectatorRailPositionStorageKey, legacy);
                    storage.removeItem(multiplayerSpectatorRailLegacyPositionStorageKey);
                    raw = legacy;
                }
                catch {
                    return parsePosition(legacy);
                }
            }
        }
        return parsePosition(raw);
    };
    const save = ({ x, y }) => {
        if (!Number.isFinite(x) || !Number.isFinite(y))
            return;
        try {
            storage?.setItem(multiplayerSpectatorRailPositionStorageKey, JSON.stringify({
                x: Math.round(x),
                y: Math.round(y),
            }));
        }
        catch { }
    };
    return Object.freeze({ load, save });
}
