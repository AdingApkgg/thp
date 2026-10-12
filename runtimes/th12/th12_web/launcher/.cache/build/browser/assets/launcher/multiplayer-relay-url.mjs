const relayRoleParams = Object.freeze([
    "room",
    "run",
    "lobby",
    "player",
    "players",
    "signal",
    "spectator",
]);
function relayUrl(value) {
    let url;
    try {
        url = new URL(value);
    }
    catch {
        throw new TypeError("invalid multiplayer relay URL");
    }
    if (url.protocol !== "ws:" && url.protocol !== "wss:") {
        throw new TypeError("multiplayer relay URL must use ws or wss");
    }
    return url;
}
function clearRelayRole(url) {
    for (const key of relayRoleParams)
        url.searchParams.delete(key);
}
export function multiplayerTransportRoomId(product, roomCode) {
    return `${product}-${roomCode}`;
}
export function buildMultiplayerLobbyRelayUrl(baseUrl, { product, roomCode, clientId }) {
    const url = relayUrl(baseUrl);
    clearRelayRole(url);
    const roomId = multiplayerTransportRoomId(product, roomCode);
    url.searchParams.set("room", roomId);
    url.searchParams.set("lobby", clientId);
    return { roomId, url: url.href };
}
export function buildMultiplayerGameplayRelayUrl(baseUrl, { product, roomCode, runId, role, }) {
    const url = relayUrl(baseUrl);
    clearRelayRole(url);
    url.searchParams.set("room", multiplayerTransportRoomId(product, roomCode));
    url.searchParams.set("run", String(Math.max(0, Math.trunc(Number(runId) || 0))));
    if ("spectator" in role)
        url.searchParams.set("spectator", role.spectator);
    else
        url.searchParams.set("player", String(role.player));
    return url.href;
}
