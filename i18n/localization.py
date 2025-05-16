import yaml
from pathlib import Path


class I18n:
    """Load every YAML file in i18n/locales and let you pull out a single-language dict."""

    def __init__(self, locales_dir: str = "i18n/locales", default_lang: str = "en"):
        base_path = Path(__file__).parent.parent
        self.locales_dir = base_path / locales_dir
        self.default_lang = default_lang
        self.translations: dict[str, dict] = {}
        self._load_translations()

    def _load_translations(self) -> None:
        for file in self.locales_dir.glob("*.yaml"):
            lang = file.stem.lower()
            with file.open(encoding="utf-8") as f:
                self.translations[lang] = yaml.safe_load(f)

    def get_locale(self, lang: str | None = None) -> dict:
        """Return the whole dictionary for one language (fallback → default_lang)."""
        lang = (lang or self.default_lang).lower()[:2]
        return self.translations.get(lang, self.translations[self.default_lang])
