export function postTouchControls(context, controls, touchSensitivity) {
    if (!context.launched || !context.ready || !context.target || context.spectator)
        return false;
    context.target.postMessage({
        protocol: context.protocol,
        game: context.game,
        command: "touch-controls",
        ...controls,
        touchSensitivity,
    }, context.targetOrigin);
    return true;
}
export function postDirectTouch(context, type, touch) {
    if (!context.launched || !context.ready || !context.target || !touch)
        return false;
    context.target.postMessage({
        protocol: context.protocol,
        game: context.game,
        command: "direct-touch",
        type,
        id: touch.id,
        x: touch.x,
        y: touch.y,
    }, context.targetOrigin);
    return true;
}
export function postTouchCancel(context) {
    if (!context.launched || !context.ready || !context.target)
        return false;
    context.target.postMessage({
        protocol: context.protocol,
        game: context.game,
        command: "touch-cancel",
    }, context.targetOrigin);
    return true;
}
export function postThpracMouse(context, type, x, y) {
    if (!context.target)
        return false;
    context.target.postMessage({
        protocol: context.protocol,
        game: context.game,
        command: "thprac-mouse",
        type,
        x,
        y,
    }, context.targetOrigin);
    return true;
}
