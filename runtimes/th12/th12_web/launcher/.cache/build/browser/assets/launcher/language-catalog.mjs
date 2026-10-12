const ORIGINAL_LANGUAGE = Object.freeze({
    id: "ja",
    title: "日本語(原版)",
    pack: null,
});
const LANGUAGE_DISPLAY_NAMES = Object.freeze({
    ja: "日本語(原版)",
    "lang_zh-hans": "中文（简体）",
    "lang_zh-hant": "中文（繁體）",
    lang_en: "English",
    lang_ru: "Русский",
});
const LANGUAGE_DISPLAY_NAME_KEYS = Object.freeze({
    ja: "gameLanguage.ja",
    "lang_zh-hans": "gameLanguage.zhHans",
    "lang_zh-hant": "gameLanguage.zhHant",
    lang_en: "gameLanguage.en",
    lang_ru: "gameLanguage.ru",
});
export function buildLanguageCatalog({ languageOptions, legacyLanguages, generation, translate, priority, }) {
    // `languageOptions` is the canonical Host Manifest selection surface.
    // `languages` predates it in schema 1 and remains read-only deployment
    // compatibility; current producers must not depend on this fallback.
    const base = Array.isArray(languageOptions)
        ? languageOptions
        : Array.isArray(legacyLanguages)
            ? [ORIGINAL_LANGUAGE, ...legacyLanguages]
            : [ORIGINAL_LANGUAGE];
    const byId = new Map();
    for (const raw of base) {
        if (!raw || typeof raw !== "object" || Array.isArray(raw))
            continue;
        const id = String(raw.id || "");
        if (!id)
            continue;
        byId.set(id, { ...raw, id });
    }
    if (!byId.has("ja"))
        byId.set("ja", { ...ORIGINAL_LANGUAGE });
    const packageLanguages = generation?.descriptor?.components?.language?.entries;
    if (Array.isArray(packageLanguages)) {
        for (const packageEntry of packageLanguages) {
            if (!packageEntry || typeof packageEntry.id !== "string" || !packageEntry.id ||
                typeof packageEntry.file !== "string" || !packageEntry.file)
                continue;
            const ref = generation?.files?.[packageEntry.file];
            if (!ref?.objectId)
                continue;
            const declaration = generation?.descriptor?.files?.[packageEntry.file];
            const existing = byId.get(packageEntry.id);
            byId.set(packageEntry.id, {
                ...(existing || { id: packageEntry.id, pack: null }),
                title: packageEntry.title || existing?.title || packageEntry.id,
                packageFile: packageEntry.file,
                packageObjectId: ref.objectId,
                packageBytes: Number(declaration?.bytes) || 0,
            });
        }
    }
    return [...byId.values()]
        .map(entry => {
        const titleKey = LANGUAGE_DISPLAY_NAME_KEYS[entry.id];
        const translated = titleKey && translate ? translate(titleKey) : "";
        return {
            ...entry,
            title: translated || LANGUAGE_DISPLAY_NAMES[entry.id] || entry.title || entry.id,
        };
    })
        .sort((a, b) => priority(a.id) - priority(b.id) || a.id.localeCompare(b.id, "en"));
}
export function selectLanguageEntry(entries, requestedId) {
    return entries.find(entry => entry.id === requestedId) || entries[0] || null;
}
export function resolveLanguagePackSource(entry, baseUrl) {
    if (!entry)
        return null;
    if (entry.packageObjectId) {
        return {
            language: entry.id,
            packageObjectId: entry.packageObjectId,
            packageFile: entry.packageFile,
            bytes: entry.packageBytes || 0,
            packageLocal: true,
        };
    }
    if (!entry.pack)
        return null;
    if (!entry.pack || typeof entry.pack !== "object" || Array.isArray(entry.pack)) {
        throw new Error("语言包清单无效");
    }
    const pack = entry.pack;
    if (typeof pack.url !== "string" || typeof pack.sha256 !== "string" || !Number.isInteger(pack.bytes)) {
        throw new Error("语言包清单无效");
    }
    return {
        ...pack,
        language: entry.id,
        url: new URL(pack.url, baseUrl).href,
        sha256: pack.sha256,
        bytes: Number(pack.bytes),
    };
}
export function thpracLocaleForLanguage(id) {
    return id === "lang_zh-hans" ? "zh-CN" : id === "ja" ? "ja-JP" : "en-US";
}
