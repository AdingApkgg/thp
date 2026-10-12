import { HOST_PROTOCOL, isGameId } from "./product-catalog.mjs";
export const RUNTIME_PROTOCOL_COMMANDS = Object.freeze([
    "configure",
    "resources",
    "keyboard",
    "keyboard-clear",
    "touch-controls",
    "touch-cancel",
    "direct-touch",
    "launch",
    "list",
    "read",
    "write",
    "remove",
    "sync",
]);
// Optional commands are capability-specific and are not required of every
// Runtime shell. They still share the same envelope and request ownership.
export const RUNTIME_PROTOCOL_OPTIONAL_COMMANDS = Object.freeze([
    "retry-music",
    "thprac-mouse",
]);
export const RUNTIME_PROTOCOL_EVENTS = Object.freeze([
    "ready",
    "transfer",
    "first-frame",
    "runtime-info",
    "frame-health",
    "exit",
    "error",
]);
export const RUNTIME_PROTOCOL_OPTIONAL_EVENTS = Object.freeze([
    "audio-health",
    "midi-fallback",
    "music-complete",
    "music-error",
    "music-incomplete",
    "player-debug",
    "thprac-session",
]);
export function isRuntimeResponseMessage(value) {
    return typeof value.request === "string" && typeof value.ok === "boolean";
}
const runtimeEvents = new Set([
    ...RUNTIME_PROTOCOL_EVENTS,
    ...RUNTIME_PROTOCOL_OPTIONAL_EVENTS,
]);
function isRecord(value) {
    return value !== null && typeof value === "object" && !Array.isArray(value);
}
export function parseRuntimeInboundMessage(value, expectedGame) {
    if (!isRecord(value) || value.protocol !== HOST_PROTOCOL || value.game !== expectedGame || !isGameId(expectedGame)) {
        return null;
    }
    if (typeof value.event === "string" && runtimeEvents.has(value.event)) {
        return value;
    }
    if (typeof value.request === "string" && typeof value.ok === "boolean") {
        return value;
    }
    return null;
}
