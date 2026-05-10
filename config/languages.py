from dataclasses import dataclass, field


@dataclass(frozen=True)
class LanguageConfig:
    """Immutable config for one target language."""

    code: str                   # e.g. "tr", "de"
    name: str                   # e.g. "Turkish", "German"
    native_name: str            # e.g. "Türkçe", "Deutsch"
    base_branch: str            # git branch to branch off from
    glossary_path: str          # path to the glossary CSV
    glossary_repo_path: str     # path to the glossary git repo
    rtl: bool = False           # right-to-left script?

    # Header translations: English key → target language value
    header_translations: dict[str, str] = field(default_factory=dict)

    # Link prefix: replaces "/en/" in hrefs
    link_prefix: str = ""

    def __post_init__(self):
        # Default link_prefix to "/<code>/" when not explicitly set
        if not self.link_prefix:
            object.__setattr__(self, "link_prefix", f"/{self.code}/")


# ──────────────────────────────────────────────────────────────────────────────
# Language registry
# ──────────────────────────────────────────────────────────────────────────────

LANGUAGES: dict[str, LanguageConfig] = {
    "tr": LanguageConfig(
        code="tr",
        name="Turkish",
        native_name="Türkçe",
        base_branch="dev-tr",
        glossary_path="glossaries/glossary_tr.csv",
        glossary_repo_path=".",
        header_translations={
            "Problem it addresses": "Hangi Sorunları Çözer",
            "How it helps": "Nasıl Yardımcı Olur",
            "Related terms": "Bağlantılı Terimler",
        },
    ),
    "de": LanguageConfig(
        code="de",
        name="German",
        native_name="Deutsch",
        base_branch="dev-de",
        glossary_path="glossaries/glossary_de.csv",
        glossary_repo_path=".",
        header_translations={
            "Problem it addresses": "Welche Probleme werden gelöst",
            "How it helps": "Wie es hilft",
            "Related terms": "Verwandte Begriffe",
        },
    ),
    "fr": LanguageConfig(
        code="fr",
        name="French",
        native_name="Français",
        base_branch="dev-fr",
        glossary_path="glossaries/glossary_fr.csv",
        glossary_repo_path=".",
        header_translations={
            "Problem it addresses": "Problèmes traités",
            "How it helps": "Comment cela aide",
            "Related terms": "Termes associés",
        },
    ),
    "es": LanguageConfig(
        code="es",
        name="Spanish",
        native_name="Español",
        base_branch="dev-es",
        glossary_path="glossaries/glossary_es.csv",
        glossary_repo_path=".",
        header_translations={
            "Problem it addresses": "Problemas que aborda",
            "How it helps": "Cómo ayuda",
            "Related terms": "Términos relacionados",
        },
    ),
    "ja": LanguageConfig(
        code="ja",
        name="Japanese",
        native_name="日本語",
        base_branch="dev-ja",
        glossary_path="glossaries/glossary_ja.csv",
        glossary_repo_path=".",
        header_translations={
            "Problem it addresses": "解決する問題",
            "How it helps": "どのように役立つか",
            "Related terms": "関連用語",
        },
    ),
}


def get_language(code: str) -> LanguageConfig:
    """Return a LanguageConfig by ISO code. Raises KeyError for unknown codes."""
    if code not in LANGUAGES:
        raise KeyError(
            f"Unknown language code '{code}'. "
            f"Available: {', '.join(LANGUAGES.keys())}"
        )
    return LANGUAGES[code]


def available_languages() -> list[tuple[str, str]]:
    """Return [(code, 'Native (English)'), ...] sorted by code."""
    return sorted(
        [(c, f"{l.native_name} ({l.name})") for c, l in LANGUAGES.items()]
    )