export function createAppShellClient({ serviceWorker = globalThis.navigator?.serviceWorker, secureContext = globalThis.isSecureContext === true, workerUrl = "./app-shell-sw.js", scope = "./", shouldDeferReload = () => false, onChange = () => { }, reload = () => globalThis.location?.reload(), schedule = callback => globalThis.setTimeout(callback, 0), logger = globalThis.console, } = {}) {
    const state = {
        registration: null,
        updateReady: false,
        updateCheckFailed: false,
        updateError: null,
        reloadPending: false,
        reloadScheduled: false,
    };
    const snapshot = () => Object.freeze({
        registration: state.registration,
        updateReady: state.updateReady,
        updateCheckFailed: state.updateCheckFailed,
        updateError: state.updateError,
        reloadPending: state.reloadPending,
        reloadScheduled: state.reloadScheduled,
    });
    const notify = () => onChange(snapshot());
    function maybeReload() {
        if (!state.updateReady || !state.reloadPending || state.reloadScheduled || shouldDeferReload())
            return false;
        state.reloadScheduled = true;
        notify();
        schedule(reload);
        return true;
    }
    function markUpdateReady({ reloadWhenPossible = false } = {}) {
        state.updateReady = true;
        state.reloadPending = true;
        notify();
        if (reloadWhenPossible)
            maybeReload();
    }
    async function checkForUpdate() {
        if (!state.registration)
            return false;
        try {
            await state.registration.update();
            state.updateCheckFailed = false;
            state.updateError = null;
            notify();
            return true;
        }
        catch (error) {
            state.updateCheckFailed = true;
            state.updateError = error;
            notify();
            logger?.warn?.("App Shell update check unavailable", error);
            return false;
        }
    }
    function watchRegistration(registration) {
        if (registration === state.registration)
            return;
        state.registration = registration;
        if (registration.waiting && serviceWorker?.controller)
            markUpdateReady();
        registration.addEventListener("updatefound", () => {
            const worker = registration.installing;
            if (!worker)
                return;
            // Capture replacement ownership at discovery time. The first install may
            // acquire a controller later through clients.claim(); that must not be
            // mistaken for an in-place update and trigger a reload loop.
            const replacingControlledWorker = !!serviceWorker?.controller;
            worker.addEventListener("statechange", () => {
                if (!replacingControlledWorker)
                    return;
                if (worker.state === "installed")
                    markUpdateReady();
                else if (worker.state === "activated")
                    markUpdateReady({ reloadWhenPossible: true });
            });
        });
        void checkForUpdate();
    }
    const ready = secureContext && serviceWorker
        ? serviceWorker.register(workerUrl, { scope, updateViaCache: "none" })
            .catch(async (error) => {
            logger?.warn?.("App Shell Service Worker unavailable; continuing without it", error);
            try {
                return await serviceWorker.getRegistration(scope);
            }
            catch {
                return null;
            }
        })
            .then(registration => {
            if (registration)
                watchRegistration(registration);
            return registration ?? null;
        })
        : Promise.resolve(null);
    return Object.freeze({
        ready,
        snapshot,
        checkForUpdate,
        maybeReload,
    });
}
