export const RESOURCE_MODE_HOSTED = "hosted";
export const RESOURCE_MODE_IMPORT = "import";
export function normalizeResourceMode(value = RESOURCE_MODE_HOSTED) {
    if (value === RESOURCE_MODE_HOSTED)
        return RESOURCE_MODE_HOSTED;
    if (value === RESOURCE_MODE_IMPORT)
        return RESOURCE_MODE_IMPORT;
    return null;
}
