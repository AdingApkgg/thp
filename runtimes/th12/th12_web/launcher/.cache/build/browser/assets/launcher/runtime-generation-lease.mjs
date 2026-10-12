export function createManagedRuntimeGenerationLease() {
    let game = null;
    let generation = null;
    let epoch = null;
    return Object.freeze({
        bind(nextGame, nextGeneration, nextEpoch = null) {
            if (!nextGame || !nextGeneration?.id || nextGeneration.game !== nextGame) {
                throw new Error("Cannot bind Managed Runtime to an invalid game generation");
            }
            if (nextEpoch !== null && (!Number.isSafeInteger(nextEpoch) || nextEpoch <= 0))
                throw new Error("Invalid Managed Runtime epoch");
            game = nextGame;
            generation = nextGeneration;
            epoch = nextEpoch;
        },
        clear() {
            game = null;
            generation = null;
            epoch = null;
        },
        resolve(request) {
            if (!generation?.id || request?.game !== game || request.generation !== generation.id || (epoch !== null && request.epoch !== epoch)) {
                throw new Error("Managed Runtime requested an inactive game generation");
            }
            return generation;
        },
    });
}
