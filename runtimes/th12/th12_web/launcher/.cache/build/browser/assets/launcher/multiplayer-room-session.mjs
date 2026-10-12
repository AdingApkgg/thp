export const multiplayerRoomSessionStorageKey = (product) => `eagler-touhou-${product}-room-v1`;
function browserSessionStorage() {
    try {
        return globalThis.sessionStorage;
    }
    catch {
        return null;
    }
}
function normalizeMaxDifficulty(value) {
    return Number.isFinite(value) ? Math.max(0, Math.trunc(value)) : 0;
}
function record(value) {
    return value !== null && typeof value === "object" && !Array.isArray(value)
        ? value
        : null;
}
export function createMultiplayerRoomSessionStore({ storage = browserSessionStorage(), } = {}) {
    const save = (product, snapshot) => {
        try {
            storage?.setItem(multiplayerRoomSessionStorageKey(product), JSON.stringify({
                product,
                room: {
                    code: snapshot.room.code,
                    playerCount: snapshot.room.playerCount,
                    difficulty: snapshot.room.difficulty,
                    created: !!snapshot.room.created,
                },
                seat: snapshot.seat,
                ready: !!snapshot.ready,
                spectatorRequested: !!snapshot.spectatorRequested,
                roomSettingsOpen: !!snapshot.roomSettingsOpen,
            }));
        }
        catch { }
    };
    const load = ({ product, roomCode, maxDifficulty }) => {
        let parsed = null;
        try {
            parsed = JSON.parse(storage?.getItem(multiplayerRoomSessionStorageKey(product)) || "null");
        }
        catch {
            return null;
        }
        const saved = record(parsed);
        const room = record(saved?.room);
        if (!saved || !room || saved.product !== product || room.code !== roomCode)
            return null;
        const playerCount = Number(room.playerCount) === 3 ? 3 : 2;
        const difficulty = Math.max(0, Math.min(normalizeMaxDifficulty(maxDifficulty), Number(room.difficulty) || 0));
        const savedSeat = saved.seat;
        const seat = typeof savedSeat === "number" && Number.isInteger(savedSeat) &&
            savedSeat >= 0 && savedSeat < playerCount
            ? savedSeat
            : null;
        return {
            product,
            room: {
                code: roomCode,
                playerCount,
                difficulty,
                created: !!room.created,
            },
            seat,
            ready: !!saved.ready,
            spectatorRequested: seat == null && !!saved.spectatorRequested,
            roomSettingsOpen: !!saved.roomSettingsOpen,
        };
    };
    const clear = (product) => {
        try {
            storage?.removeItem(multiplayerRoomSessionStorageKey(product));
        }
        catch { }
    };
    return Object.freeze({ save, load, clear });
}
