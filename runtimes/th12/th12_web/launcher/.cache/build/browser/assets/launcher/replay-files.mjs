export const replayImportAccept = ".zip,.rpy,.rpyx";
function replayExtension(name) {
    const match = /\.rpyx?$/i.exec(name);
    if (!match)
        return null;
    return match[0].toLowerCase() === ".rpyx" ? ".rpyx" : ".rpy";
}
function basename(path) {
    return path.slice(path.lastIndexOf("/") + 1);
}
function escapeRegExp(value) {
    return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
function normalizedPathSet(paths) {
    return new Set([...paths].map(path => String(path).toLowerCase().replace(/\.rpyx$/, ".rpy")));
}
export function isSafeReplayArchivePath(value) {
    return typeof value === "string" && value.length > 0 && value.length <= 240 &&
        !value.includes("\\") && !value.startsWith("/") &&
        !value.split("/").some(part => !part || part === "." || part === "..");
}
export function isReplayFilePath(path) {
    return typeof path === "string" && /^replay\/[^/]+\.rpyx?$/i.test(path);
}
export function selectReplayExportPaths(paths) {
    return [...paths].map(String).filter(isReplayFilePath).sort((a, b) => a.localeCompare(b));
}
export function isValidReplayName(prefix, name) {
    if (typeof name !== "string" || !prefix)
        return false;
    return new RegExp(`^${escapeRegExp(prefix)}_(?:\\d{2}|ud[0-9a-f]{4})\\.rpyx?$`, "i").test(name);
}
export function sanitizeReplayImportName(name) {
    return String(name).replace(/[^\w.()-]/g, "_");
}
export function isReplayTargetAvailable(existingPaths, targetPath) {
    if (!isReplayFilePath(targetPath))
        return false;
    const occupied = normalizedPathSet(existingPaths);
    return !occupied.has(targetPath.toLowerCase().replace(/\.rpyx$/, ".rpy"));
}
export function allocateReplayName(prefix, existingPaths, sourceName) {
    const extension = replayExtension(sourceName);
    if (!extension)
        return null;
    const sanitized = sanitizeReplayImportName(sourceName);
    if (isValidReplayName(prefix, sanitized)) {
        const target = `replay/${sanitized}`;
        if (isReplayTargetAvailable(existingPaths, target))
            return sanitized;
    }
    const occupied = normalizedPathSet(existingPaths);
    for (let index = 0; index <= 0xffff; index++) {
        const name = `${prefix}_ud${index.toString(16).padStart(4, "0")}${extension}`;
        const target = `replay/${name}`;
        if (!occupied.has(target.toLowerCase().replace(/\.rpyx$/, ".rpy")))
            return name;
    }
    return null;
}
export function isReplayImportFileName(name) {
    return typeof name === "string" && /\.(?:rpyx?|zip)$/i.test(name);
}
export function planReplayArchiveImport(prefix, archivePaths, existingPaths) {
    const filePaths = [...archivePaths].map(String).filter(path => !path.endsWith("/"));
    if (filePaths.some(path => !isSafeReplayArchivePath(path)))
        return { ok: false, reason: "unsafe-path" };
    const archiveByLower = new Map();
    for (const path of filePaths) {
        const lower = path.toLowerCase().replace(/\.rpyx$/, ".rpy");
        if (archiveByLower.has(lower))
            return { ok: false, reason: "duplicate-path" };
        archiveByLower.set(lower, path);
    }
    const occupied = [...existingPaths].map(String);
    const entries = [];
    const replaySources = filePaths
        .filter(path => replayExtension(basename(path)) !== null)
        .sort((a, b) => a.localeCompare(b));
    for (const sourcePath of replaySources) {
        const name = allocateReplayName(prefix, occupied, basename(sourcePath));
        if (!name)
            return { ok: false, reason: "slots-exhausted" };
        const targetPath = `replay/${name}`;
        entries.push({ sourcePath, targetPath, kind: "replay" });
        occupied.push(targetPath);
    }
    return { ok: true, entries };
}
