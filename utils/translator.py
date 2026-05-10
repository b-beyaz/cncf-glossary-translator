import os
import requests
import anthropic
from dotenv import load_dotenv
from urllib.parse import urlparse

from config.languages import LanguageConfig, get_language
from utils.file_ops import read_glossary
from utils.logger import logger

load_dotenv()


class CNCFTranslator:
    def __init__(self):
        vertex_project_id = os.getenv("ANTHROPIC_VERTEX_PROJECT_ID")

        if vertex_project_id:
            region = os.getenv("CLOUD_ML_REGION", "us-east5")
            logger.info(f"Vertex AI (project: {vertex_project_id}, region: {region})")
            self.client = anthropic.AnthropicVertex(
                project_id=vertex_project_id, region=region
            )
            self.model = os.getenv("MODEL_NAME", "claude-sonnet-4-5@20250929")
        else:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError(
                    "Set ANTHROPIC_API_KEY or ANTHROPIC_VERTEX_PROJECT_ID."
                )
            logger.info("Direct Anthropic API")
            self.client = anthropic.Anthropic(api_key=api_key)
            self.model = os.getenv("MODEL_NAME", "claude-sonnet-4-20250514")

        logger.info(f"Model: {self.model}")

    # ── URL helpers ────────────────────────────────────────────────────────────

    def get_raw_url(self, url: str) -> str:
        return (
            url.replace("https://github.com/", "https://raw.githubusercontent.com/")
               .replace("/edit/", "/")
               .replace("/blob/", "/")
        )

    def get_filename_from_url(self, url: str) -> str:
        return os.path.basename(urlparse(url).path)

    # ── Core translation ───────────────────────────────────────────────────────

    def translate(
        self,
        url: str,
        lang: LanguageConfig | None = None,
    ) -> tuple[str, str]:
        """
        Translate the markdown file at *url* into the target language.

        Args:
            url:  GitHub URL of the source English file.
            lang: LanguageConfig for the target language.
                  Falls back to the LANGUAGE env var, then "tr".

        Returns:
            (translation_markdown, suggestions_raw_text)
        """
        if lang is None:
            env_code = os.getenv("LANGUAGE", "tr")
            lang = get_language(env_code)

        raw_url = self.get_raw_url(url)
        response = requests.get(raw_url)
        if response.status_code != 200:
            return (
                f"Error: Could not fetch source file. (HTTP {response.status_code})",
                "",
            )

        source_text = response.text
        glossary = read_glossary(lang.glossary_path)

        system_msg = self._build_system_prompt(lang, glossary)

        try:
            api_response = self.client.messages.create(
                model=self.model,
                max_tokens=8192,
                system=system_msg,
                messages=[{"role": "user", "content": source_text}],
            )

            full_response = api_response.content[0].text
            logger.debug(f"Response tail:\n{full_response[-300:]}")

            if "SUGGESTIONS:" in full_response:
                translation, suggestions_raw = full_response.split("SUGGESTIONS:", 1)
                translation = translation.strip()
                suggestions_raw = suggestions_raw.strip()
                logger.info("Term suggestions found.")
            else:
                translation = full_response.strip()
                suggestions_raw = ""
                logger.warning("No suggestions block found.")

            return translation, suggestions_raw

        except Exception as exc:
            logger.error(f"API error: {exc}")
            return f"API Error: {exc}", ""

    # ── Prompt builder ─────────────────────────────────────────────────────────

    def _build_system_prompt(self, lang: LanguageConfig, glossary: str) -> str:
        header_rules = "\n".join(
            f'           - "{en}" → "{target}"'
            for en, target in lang.header_translations.items()
        )
        rtl_note = (
            "\n        8. RTL: This language is written right-to-left. "
            "Ensure punctuation and directionality are correct."
            if lang.rtl
            else ""
        )

        return f"""
        You are a professional CNCF Glossary translator specialising in Cloud Native technologies.
        Target language: {lang.name} ({lang.native_name})

        RULES:
        1. GLOSSARY: Strictly follow the provided glossary. Do not deviate:
        {glossary}

        2. LINKS: Convert [Text](/en/path/) → [Translated Text]({lang.link_prefix}path/).
           Only translate the visible text and change '/en/' to '{lang.link_prefix}'.
           Example (Turkish):  [API Gateway](/en/api-gateway/) → [API Geçidi](/tr/api-gateway/)

        3. FORMAT:
           - Headers: always one space after '#' (e.g. '## Header').
           - Spacing: exactly one blank line between paragraphs.
           - Frontmatter: keep YAML structure intact.
             For 'title', 'category', and 'tags' VALUES:
               1. Check local glossary first.
               2. If not in glossary, use the {lang.name} IT/DevOps industry standard.
               3. Never translate the KEYS (title:, category:, tags:).
               4. Keep tags comma-separated and technically accurate.

        4. SPECIFIC HEADERS (translate exactly as shown):
        {header_rules}

        5. LANGUAGE: Use a professional, technical, yet accessible tone in {lang.name}
           suitable for the CNCF community.

        6. TRANSLATION POLICY:
           - NEVER leave technical concepts in English unless they are international
             units or acronyms (HTTP, gRPC, IP, etc.).
           - Avoid robotic literal translations; use proper DevOps/cloud-native terminology.

        7. TERM SUGGESTIONS
           Analyse the source for technical terms NOT in the glossary.
           - Only suggest cloud-native / DevOps-specific terms.
           - Do NOT suggest terms already in the glossary.
           - Place suggestions at the VERY END of your response in this format:

             SUGGESTIONS:
             English Term | {lang.name} Translation
        {rtl_note}

        Return ONLY the translated markdown content followed (if applicable) by the
        SUGGESTIONS block. No preamble, no closing remarks.
        """


# ── CLI entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from config.languages import available_languages, get_language

    print("Available languages:")
    for code, label in available_languages():
        print(f"  {code}: {label}")

    lang_code = input("\nLanguage code (e.g. tr, de, ar): ").strip() or "tr"
    target_lang = get_language(lang_code)

    translator = CNCFTranslator()
    target_url = input("GitHub file URL: ").strip()

    filename = translator.get_filename_from_url(target_url)
    if not filename.endswith(".md"):
        filename = "translated_output.md"

    print(f"\nTranslating → {target_lang.name} …")
    translation, suggestions = translator.translate(target_url, lang=target_lang)

    out_file = f"{lang_code}_{filename}"
    with open(out_file, "w", encoding="utf-8") as fh:
        fh.write(translation)

    print(f"\nSaved to '{out_file}'.")
    if suggestions:
        print("\nSuggested terms:\n" + suggestions)