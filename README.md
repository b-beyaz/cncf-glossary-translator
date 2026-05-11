# CNCF Glossary AI Suite

A Streamlit application that translates CNCF Glossary markdown files from English into any target language using Claude AI — while enforcing approved terminology, handling Git operations automatically, and continuously building a language-specific glossary.

---

## Features

- **AI-powered translation** via Claude (Anthropic API or Vertex AI)
- **Glossary enforcement** — approved terms are injected into every prompt
- **Multi-language support** — add a new language with a single config entry
- **Automatic link conversion** — `/en/` paths become `/tr/`, `/de/`, `/ar/` etc.
- **Header mapping** — standard CNCF headers translated consistently per language
- **Term suggestions** — Claude proposes missing glossary entries after each translation
- **One-click Git workflow** — branch creation, commit, and push handled automatically
- **Two editing flows** — new translation from URL, or edit files on an existing branch

---

## Project Structure

```
.
├── app.py                   # Streamlit entrypoint
├── config/
│   ├── __init__.py
│   └── languages.py         # LanguageConfig definitions for all languages
├── utils/
│   ├── __init__.py
│   ├── file_ops.py          # Git helpers, glossary I/O, UI utilities
│   ├── translator.py        # CNCFTranslator — Claude API wrapper
│   ├── ui_components.py     # StepManager, render_file_uploader
│   └── logger.py            # Centralized logging setup
├── glossaries/
│   ├── glossary_tr.csv      # Turkish glossary
│   ├── glossary_de.csv      # German glossary
│   ├── glossary_ar.csv      # Arabic glossary
│   └── ...                  # One CSV per language
├── styles/
│   └── main.css
├── logs/
│   └── app.log
├── .env                     # Local secrets (not committed)
├── .env.example             # Template for required env variables
├── docker-compose.yml
└── Dockerfile
```

---

## Quickstart

### 1. Clone the repo

```bash
git clone https://github.com/b-beyaz/cncf-glossary-translator.git
cd cncf-glossary-translator
```

### 2. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env` with your values (see [Environment Variables](#environment-variables) below).

### 3. Run with Docker

```bash
docker compose up --build
```

The app will be available at `http://localhost:8501`.

### 4. Run locally (without Docker)

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes* | Anthropic API key for Claude |
| `ANTHROPIC_VERTEX_PROJECT_ID` | Yes* | GCP project ID (Vertex AI alternative) |
| `CLOUD_ML_REGION` | No | Vertex AI region (default: `us-east5`) |
| `MODEL_NAME` | No | Claude model to use (default: `claude-sonnet-4-20250514`) |
| `REPO_PATH` | Yes | Absolute path to the local CNCF glossary repo |
| `OUTPUT_DIR` | Yes | Directory where translated `.md` files are saved |
| `GITHUB_TOKEN` | Yes | GitHub PAT with repo write access |
| `GITHUB_NAME` | Yes | GitHub org or username (used in remote URL) |
| `GITHUB_USER` | Yes | GitHub username (for git credentials) |
| `GITHUB_EMAIL` | Yes | Email for git commits |
| `GLOSSARY_REPO_PATH` | Yes | Path to the repo containing glossary CSVs |
| `LANGUAGE` | No | Default language code on startup (default: `tr`) |

*Set either `ANTHROPIC_API_KEY` **or** `ANTHROPIC_VERTEX_PROJECT_ID`, not both.

---

## Adding a New Language

Open `config/languages.py` and add one entry to the `LANGUAGES` dict:

```python
"ko": LanguageConfig(
    code="ko",
    name="Korean",
    native_name="한국어",
    base_branch="dev-ko",
    glossary_path="glossaries/glossary_ko.csv",
    glossary_repo_path=".",
    header_translations={
        "Problem it addresses": "해결하는 문제",
        "How it helps": "어떻게 도움이 되는가",
        "Related terms": "관련 용어",
    },
),
```

That's it. No other file needs to change — the app, translator, and Git automation all adapt automatically.

For right-to-left languages (Arabic, Hebrew etc.) add `rtl=True`:

```python
"he": LanguageConfig(
    ...
    rtl=True,
    ...
),
```

---

## Workflows

### Flow 1 — New Translation

1. Select the target language from the sidebar
2. Paste a GitHub URL to any English `.md` file in the CNCF glossary repo
3. Click **Translate** — Claude translates the file with glossary enforcement
4. Review and edit the result in the built-in markdown editor
5. Set a branch name and commit message
6. Click **Push to Remote** — the branch is created and pushed automatically

### Flow 2 — Edit Existing Branch

1. Select a local branch from the dropdown and click **Switch & Pull**
2. Pick one or more files from the repo file explorer
3. Edit content in the inline text editor
4. Enter a commit message and click **Push all changes**

---

## Glossary System

Each language has its own CSV file under `glossaries/`:

```
glossaries/
├── glossary_tr.csv
├── glossary_de.csv
└── glossary_ar.csv
```

**CSV format:**

```csv
English,Translation,Notes
API Gateway,API Geçidi,
Container,Konteyner,approved 2024
```

### How glossary terms are enforced

The glossary is read before every translation and injected into the Claude system prompt as a markdown table. Any term present in the glossary is used verbatim — Claude is instructed never to deviate from approved translations.

### AI term suggestions

After each translation Claude identifies technical terms that are missing from the glossary and proposes translations. These appear in the sidebar under **Proposed New Terms**. Reviewers can:

- Edit the suggested translation inline
- Tick the terms they approve
- Click **Add Selected** — terms are written to the CSV and pushed to remote automatically

---

## Supported Languages (pre-configured)

| Code | Language | Branch | Glossary |
|---|---|---|---|
| `tr` | Turkish / Türkçe | `dev-tr` | `glossaries/glossary_tr.csv` |
| `de` | German / Deutsch | `dev-de` | `glossaries/glossary_de.csv` |
| `fr` | French / Français | `dev-fr` | `glossaries/glossary_fr.csv` |
| `es` | Spanish / Español | `dev-es` | `glossaries/glossary_es.csv` |
| `ja` | Japanese / 日本語 | `dev-ja` | `glossaries/glossary_ja.csv` |

---

## Requirements

- Python 3.11+
- Git (configured with access to the target repo)
- An Anthropic API key **or** a GCP project with Vertex AI enabled

Key Python dependencies:

```
streamlit
anthropic
gitpython
pandas
tabulate
python-dotenv
requests
```

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-change`
3. Commit your changes: `git commit -m "Add: my change"`
4. Push and open a pull request

---

## License

Apache 2.0 — see [LICENSE](LICENSE) for details.
