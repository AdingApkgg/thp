export const PLAYER_HISTORY_KEY = "eaglerTouhouPlayer";
export const MP_ROOM_HISTORY_KEY = "eaglerTouhouMpRoom";
export const MP_ROOM_URL_KEY = "mpRoom";
function historyState(value) {
    return value !== null && typeof value === "object" && !Array.isArray(value)
        ? { ...value }
        : {};
}
export function normalizeRoomCode(value) {
    return String(value || "").replace(/\D/g, "").slice(0, 8);
}
export function routedProductFromUrl(source, productIds) {
    const value = new URL(source).searchParams.get("game");
    return value !== null && productIds.has(value) ? value : null;
}
export function launcherHomeUrl(source) {
    const url = new URL(source);
    url.searchParams.delete("game");
    url.searchParams.delete(MP_ROOM_URL_KEY);
    return url;
}
export function launcherHomeHistoryState(currentState) {
    const next = historyState(currentState);
    next[PLAYER_HISTORY_KEY] = false;
    next[MP_ROOM_HISTORY_KEY] = false;
    delete next.game;
    return next;
}
export function launcherHomeHistoryOperation({ currentUrl, currentState, }) {
    return {
        kind: "replace",
        state: launcherHomeHistoryState(currentState),
        url: launcherHomeUrl(currentUrl).href,
    };
}
export function playerRouteUrl(source, product) {
    const url = new URL(source);
    url.searchParams.set("game", product);
    return url;
}
export function roomRouteUrl(source, product, roomCode) {
    const url = playerRouteUrl(source, product);
    url.searchParams.set(MP_ROOM_URL_KEY, roomCode);
    return url;
}
export function roomRouteHistoryOperation({ currentUrl, currentState, product, roomCode, push = false, }) {
    const url = new URL(currentUrl);
    if (roomCode) {
        url.searchParams.set(MP_ROOM_URL_KEY, roomCode);
        url.searchParams.set("game", product);
    }
    else {
        url.searchParams.delete(MP_ROOM_URL_KEY);
    }
    const nextState = historyState(currentState);
    nextState[MP_ROOM_HISTORY_KEY] = roomCode || false;
    return { kind: push ? "push" : "replace", state: nextState, url: url.href };
}
export function returnToRoomHistoryOperation({ currentUrl, currentState, product, roomCode, }) {
    const url = roomRouteUrl(currentUrl, product, roomCode);
    const nextState = historyState(currentState);
    nextState[PLAYER_HISTORY_KEY] = false;
    nextState[MP_ROOM_HISTORY_KEY] = roomCode;
    nextState.game = product;
    return { kind: "replace", state: nextState, url: url.href };
}
export function initialRoutedHistoryOperations({ currentUrl, currentState, routedProduct, navigationType, multiplayerProduct, }) {
    if (navigationType === "reload") {
        const reloadUrl = new URL(currentUrl);
        const reloadRoom = normalizeRoomCode(reloadUrl.searchParams.get(MP_ROOM_URL_KEY));
        const reloadState = historyState(currentState);
        reloadState[PLAYER_HISTORY_KEY] = false;
        if (reloadRoom && multiplayerProduct) {
            reloadUrl.searchParams.set("game", routedProduct);
            reloadState.game = routedProduct;
            reloadState[MP_ROOM_HISTORY_KEY] = reloadRoom;
        }
        else {
            reloadUrl.searchParams.delete("game");
            delete reloadState.game;
        }
        return [{ kind: "replace", state: reloadState, url: reloadUrl.href }];
    }
    const previous = historyState(currentState);
    if (previous[PLAYER_HISTORY_KEY])
        return [];
    const gameUrl = new URL(currentUrl);
    const homeUrl = new URL(currentUrl);
    homeUrl.searchParams.delete("game");
    return [
        {
            kind: "replace",
            state: { ...previous, [PLAYER_HISTORY_KEY]: false },
            url: homeUrl.href,
        },
        {
            kind: "push",
            state: { [PLAYER_HISTORY_KEY]: true, game: routedProduct },
            url: gameUrl.href,
        },
    ];
}
export function playerRouteHistoryOperation({ currentUrl, currentState, routedProduct, product, }) {
    const previous = historyState(currentState);
    const url = playerRouteUrl(currentUrl, product);
    const nextState = { ...previous, [PLAYER_HISTORY_KEY]: true, game: product };
    if (!previous[PLAYER_HISTORY_KEY])
        return { kind: "push", state: nextState, url: url.href };
    if (routedProduct !== product || previous.game !== product) {
        return { kind: "replace", state: nextState, url: url.href };
    }
    return null;
}
export function directRoomHistorySeed({ currentUrl, currentState, roomCode, }) {
    const previous = historyState(currentState);
    if (previous[MP_ROOM_HISTORY_KEY])
        return [];
    const roomUrl = new URL(currentUrl);
    const homeState = launcherHomeHistoryState(previous);
    return [
        { kind: "replace", state: homeState, url: launcherHomeUrl(roomUrl).href },
        {
            kind: "push",
            state: { ...homeState, [MP_ROOM_HISTORY_KEY]: roomCode },
            url: roomUrl.href,
        },
    ];
}
export function applyHistoryOperations(historyObj, operations) {
    for (const operation of operations) {
        if (operation.kind === "replace")
            historyObj.replaceState(operation.state, "", operation.url);
        else
            historyObj.pushState(operation.state, "", operation.url);
    }
}
