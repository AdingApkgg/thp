export function resolveMusicMode({ requested = "ogg-stream", explicit = false, audio = true, midi = true, localOgg = false, remoteOgg = false, preferOgg = true, } = {}) {
    if (!audio || requested === "none")
        return "none";
    const ogg = localOgg || remoteOgg;
    if (explicit && requested === "midi" && midi)
        return "midi";
    if ((requested === "ogg-stream" || requested === "ogg-full") && ogg)
        return requested;
    if (!explicit && ogg && preferOgg)
        return "ogg-stream";
    if (midi)
        return "midi";
    return ogg ? "ogg-stream" : "none";
}
export function resolveMusicAvailability({ audio, midiAvailable, importServer, publishedOggCapable, remoteOggAdvertised, remoteRevision = null, installed = null, }) {
    let localOgg = false;
    let remoteOgg = false;
    if (installed) {
        const ids = installed.oggFileIds;
        // A local Package generation is authoritative for its own optional OGG
        // component. Local availability must not depend on whether the current
        // Host also publishes an OGG/WAV resource set.
        localOgg = ids.length > 0 && ids.every(fileId => !!installed.files[fileId]?.objectId);
        // Completing a partial local generation from the network is different:
        // the current publication must explicitly support OGG and match the
        // generation identity before remote files may be considered available.
        remoteOgg = publishedOggCapable && !importServer && ids.length >= 2 && remoteRevision === installed.revision;
    }
    else if (!importServer) {
        remoteOgg = remoteOggAdvertised;
    }
    return {
        audio,
        midi: audio && midiAvailable,
        localOgg: audio && localOgg,
        remoteOgg: audio && remoteOgg,
        ogg: audio && (localOgg || remoteOgg),
    };
}
export function resolveEffectiveMusicMode({ requested, explicit, audio, midiAvailable, importServer, publishedOggCapable, remoteOggAdvertised, remoteRevision = null, installed = null, }) {
    const availability = resolveMusicAvailability({
        audio,
        midiAvailable,
        importServer,
        publishedOggCapable,
        remoteOggAdvertised,
        remoteRevision,
        installed,
    });
    return resolveMusicMode({
        requested,
        explicit,
        audio: availability.audio,
        midi: availability.midi,
        localOgg: availability.localOgg,
        remoteOgg: availability.remoteOgg,
        preferOgg: availability.localOgg || (!installed && !importServer),
    });
}
