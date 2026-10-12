export const DEFAULT_GAME_OPTIONS = Object.freeze({
    thpracEnabled: false,
    thpracTouchControlsEnabled: false,
    magnifierEnabled: false,
    th06FocusHitbox: false,
    frameLimit60Enabled: false,
    touchEnabled: false,
    touchMovementMode: "touch",
    touchSensitivity: 100,
    touchFocusMode: "hold-button",
    doubleTapBombEnabled: false,
    alwaysHitbox: false,
    enhanceLocalPlayerVisibility: false,
});
export const TOUCH_MOVEMENT_MODES = new Set([
    "touch", "touch-unlimited", "joystick", "joystick-free",
]);
export const TOUCH_FOCUS_MODES = new Set([
    "two-finger", "hold-button", "toggle-button",
]);
export const MUSIC_MODES = new Set(["ogg-stream", "ogg-full", "midi", "none"]);
export function isMusicMode(value) {
    return value === "ogg-stream" || value === "ogg-full" || value === "midi" || value === "none";
}
export function isTouchMovementMode(value) {
    return value === "touch" || value === "touch-unlimited" || value === "joystick" || value === "joystick-free";
}
export function isTouchFocusMode(value) {
    return value === "two-finger" || value === "hold-button" || value === "toggle-button";
}
export const gamePreferenceStorageKey = (preferenceId) => `eagler-touhou-game-options-v1-${preferenceId}`;
export const languagePreferenceStorageKey = (preferenceId) => `eagler-touhou-language-v1-${preferenceId}`;
export function touchMovementUsesJoystick(mode) {
    return mode === "joystick" || mode === "joystick-free";
}
function record(value) {
    return value !== null && typeof value === "object" && !Array.isArray(value)
        ? value
        : null;
}
function booleanOption(source, name, fallback) {
    const value = source?.[name];
    return typeof value === "boolean" ? value : fallback;
}
function normalizeMusicMode(value) {
    const legacy = value === "ogg" || value === "wav" ? "ogg-stream" : value;
    return typeof legacy === "string" && MUSIC_MODES.has(legacy)
        ? legacy
        : "ogg-stream";
}
export function normalizeStoredGamePreferences(savedValue, context) {
    const saved = record(savedValue);
    const savedOptions = record(saved?.options);
    let sanitizedRecord = saved;
    let storageRewriteRequired = false;
    if (saved && savedOptions && Object.prototype.hasOwnProperty.call(savedOptions, "limitPresentationTo60")) {
        const sanitizedOptions = { ...savedOptions };
        delete sanitizedOptions.limitPresentationTo60;
        sanitizedRecord = { ...saved, options: sanitizedOptions };
        storageRewriteRequired = true;
    }
    const rawOptions = record(sanitizedRecord?.options);
    const movementCandidate = rawOptions?.touchMovementMode;
    const migratedMovement = typeof movementCandidate === "string" &&
        TOUCH_MOVEMENT_MODES.has(movementCandidate)
        ? movementCandidate
        : rawOptions?.unlimitedTouch === true ? "touch-unlimited" : "touch";
    const focusCandidate = rawOptions?.touchFocusMode;
    let focusMode = typeof focusCandidate === "string" &&
        TOUCH_FOCUS_MODES.has(focusCandidate)
        ? focusCandidate
        : "hold-button";
    if (touchMovementUsesJoystick(migratedMovement) && focusMode === "two-finger")
        focusMode = "hold-button";
    const sensitivityCandidate = rawOptions?.touchSensitivity;
    const touchSensitivity = typeof sensitivityCandidate === "number" && Number.isFinite(sensitivityCandidate)
        ? Math.min(300, Math.max(50, Math.round(sensitivityCandidate)))
        : DEFAULT_GAME_OPTIONS.touchSensitivity;
    const options = {
        thpracEnabled: context.thpracAvailable && booleanOption(rawOptions, "thpracEnabled", DEFAULT_GAME_OPTIONS.thpracEnabled),
        thpracTouchControlsEnabled: booleanOption(rawOptions, "thpracTouchControlsEnabled", DEFAULT_GAME_OPTIONS.thpracTouchControlsEnabled),
        magnifierEnabled: booleanOption(rawOptions, "magnifierEnabled", DEFAULT_GAME_OPTIONS.magnifierEnabled),
        th06FocusHitbox: booleanOption(rawOptions, "th06FocusHitbox", DEFAULT_GAME_OPTIONS.th06FocusHitbox),
        frameLimit60Enabled: booleanOption(rawOptions, "frameLimit60Enabled", DEFAULT_GAME_OPTIONS.frameLimit60Enabled),
        touchEnabled: booleanOption(rawOptions, "touchEnabled", DEFAULT_GAME_OPTIONS.touchEnabled),
        touchMovementMode: migratedMovement,
        touchSensitivity,
        touchFocusMode: focusMode,
        doubleTapBombEnabled: booleanOption(rawOptions, "doubleTapBombEnabled", DEFAULT_GAME_OPTIONS.doubleTapBombEnabled),
        alwaysHitbox: booleanOption(rawOptions, "alwaysHitbox", DEFAULT_GAME_OPTIONS.alwaysHitbox),
        enhanceLocalPlayerVisibility: booleanOption(rawOptions, "enhanceLocalPlayerVisibility", DEFAULT_GAME_OPTIONS.enhanceLocalPlayerVisibility),
    };
    const musicPreference = normalizeMusicMode(sanitizedRecord?.music);
    const musicPreferenceExplicit = sanitizedRecord?.musicPreferenceExplicit === true;
    return Object.freeze({
        options,
        musicPreferenceExplicit,
        musicPreference,
        music: context.webAudioAvailable ? musicPreference : "none",
        sanitizedRecord,
        storageRewriteRequired,
    });
}
export function serializeGamePreferences(input) {
    return {
        music: input.musicPreferenceExplicit ? input.musicPreference : input.music,
        musicPreferenceExplicit: input.musicPreferenceExplicit,
        options: Object.fromEntries(Object.keys(DEFAULT_GAME_OPTIONS).map(name => [
            name,
            input.options[name],
        ])),
    };
}
function readStoredJson(storage, key) {
    if (!storage)
        return null;
    try {
        return JSON.parse(storage.getItem(key) || "null");
    }
    catch {
        return null;
    }
}
function readStoredString(storage, key) {
    if (!storage)
        return null;
    try {
        return storage.getItem(key);
    }
    catch {
        return null;
    }
}
export function loadStoredGamePreferences({ storage, preferenceId, fallbackPreferenceId = null, context, }) {
    let saved = readStoredJson(storage, gamePreferenceStorageKey(preferenceId));
    if (!saved && fallbackPreferenceId) {
        saved = readStoredJson(storage, gamePreferenceStorageKey(fallbackPreferenceId));
    }
    const normalized = normalizeStoredGamePreferences(saved, context);
    if (normalized.storageRewriteRequired && storage) {
        try {
            storage.setItem(gamePreferenceStorageKey(preferenceId), JSON.stringify(normalized.sanitizedRecord));
        }
        catch { }
    }
    return normalized;
}
export function loadStoredLanguagePreference({ storage, preferenceId, fallbackPreferenceId = null, }) {
    let saved = readStoredString(storage, languagePreferenceStorageKey(preferenceId));
    if (!saved && fallbackPreferenceId) {
        saved = readStoredString(storage, languagePreferenceStorageKey(fallbackPreferenceId));
    }
    return saved;
}
export function persistStoredGamePreferences({ storage, preferenceId, preferences, language, }) {
    if (!storage)
        return;
    try {
        storage.setItem(gamePreferenceStorageKey(preferenceId), JSON.stringify(serializeGamePreferences(preferences)));
    }
    catch { }
    try {
        storage.setItem(languagePreferenceStorageKey(preferenceId), language);
    }
    catch { }
}
