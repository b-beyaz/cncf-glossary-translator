# CNCF Glossary Turkish Translator

An automated localization tool designed specifically for the [CNCF Glossary](https://glossary.cncf.io/). This tool ensures consistency in cloud-native terminology by leveraging a local glossary and the Anthropic Claude model.

## Quick Start

```bash
# Clone and setup
git clone https://github.com/b-beyaz/cncf-glossary-translator.git
cd cncf-glossary-translator
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install and configure
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your credentials

# Run the web interface
streamlit run app.py
```

## Features

- **Flow 1 — New Translation:** Paste a GitHub URL of an English CNCF Glossary markdown file, review and edit the AI-generated Turkish translation, then push it to a new branch on the CNCF Glossary repository.
- **Flow 2 — Edit Existing Branch:** Switch to any local branch, select files from your computer, edit them, and push all changes in a single commit.
- **Glossary Management:** Add English–Turkish term pairs (with optional notes) directly from the sidebar. Duplicate entries are automatically prevented.
- **Sync Glossary:** Push your local `glossary.csv` to the `main` branch of the `cncf-glossary-translator` repository with a single click.
- **Markdown Header Logic:** Automatically converts specific headers like "Problem it addresses" to their standard Turkish equivalents.
- **Smart Link Conversion:** Transforms English internal links (`/en/`) to Turkish (`/tr/`) while translating the anchor text.
- **Dynamic File Naming:** Parses the GitHub URL to name the output file accordingly (e.g., `multitenancy.md`).
- **YAML Frontmatter Support:** Translates metadata values (title, category, tags) while preserving the YAML keys.

## Prerequisites

- Python 3.8+
- Authentication (choose one):
  - **Option 1:** Anthropic API Key (with access to Claude Sonnet) — recommended for most users
  - **Option 2:** Google Cloud Platform account with Vertex AI enabled — for enterprise users
- A GitHub Personal Access Token (PAT) with `repo` scope
- Local clone of the [CNCF Glossary repository](https://github.com/cncf/glossary)

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/b-beyaz/cncf-glossary-translator.git
cd cncf-glossary-translator
```

### 2. Create and activate a virtual environment

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
cp .env.example .env
```

Edit the `.env` file:

```dotenv
# Option 1: Direct Anthropic API
ANTHROPIC_API_KEY=your_api_key_here

# Option 2: Google Cloud Vertex AI
# ANTHROPIC_VERTEX_PROJECT_ID=your-gcp-project-id
# CLOUD_ML_REGION=us-east5

# Git configuration
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_USER=your_github_username

# Path to your local clone of the CNCF Glossary repository
REPO_PATH=/your/path/to/glossary

# The base branch to create new translation branches from
BASE_BRANCH=dev-tr

# Directory where translated files will be saved
OUTPUT_DIR=/your/path/to/glossary/content/tr

# Path to this repository (used for syncing glossary.csv to remote)
GLOSSARY_REPO_PATH=/your/path/to/cncf-glossary-translator
```

### 5. Prepare your glossary file

The glossary is stored as `glossary.csv` in the root of this repository with three columns:

| English | Turkish | Notes |
|---------|---------|-------|
| Cloud | Bulut | |
| Container | Konteyner | |

You can manage glossary terms directly from the sidebar in the web interface.

## Usage

### Flow 1 — New Translation

1. Open the app and select **Flow 1 — New Translation**
2. Paste the GitHub URL of the English markdown file you want to translate  
   Example: `https://github.com/cncf/glossary/blob/main/content/en/api-gateway.md`
3. Click **Translate** and wait for the AI to generate the Turkish translation
4. Review and edit the translation in the editor
5. Set a branch name and commit message
6. Click **Push to Remote** to create a new branch and push the file

### Flow 2 — Edit Existing Branch

1. Select **Flow 2 — Edit Existing Branch**
2. Choose a local branch from the dropdown and click **Switch & Pull**
3. Click **Add File From My Computer** to select one or more files
4. Edit the file contents in the editor
5. Enter a commit message and click **Push all changes**

### Glossary Management

- Use the **➕ Add Term to Glossary** panel in the sidebar to add new English–Turkish pairs
- Optionally add a note in the **Notes** field
- Click **☁️ Sync Glossary** to push `glossary.csv` to the `main` branch of this repository

## Model Configuration

By default the tool uses:
- **Direct API:** `claude-sonnet-4-20250514`
- **Vertex AI:** `claude-sonnet-4-5@20250929`

To override, add to your `.env`:
```dotenv
MODEL_NAME=your-model-name
```

### Finding available Vertex AI models

- Visit the [Vertex AI Model Garden](https://console.cloud.google.com/vertex-ai/model-garden/anthropic)
- Check [Anthropic's Vertex AI documentation](https://docs.anthropic.com/en/api/claude-on-vertex-ai)
- If using Claude Code with Vertex AI, type `/model` in any conversation

Common Vertex AI model identifiers:
- `claude-sonnet-4-5@20250929`
- `claude-3-5-sonnet@20240620`
- `claude-3-5-sonnet-v2@20241022`
- `claude-3-opus@20240229`
- `claude-3-haiku@20240307`

## Deactivating the Virtual Environment

```bash
deactivate
```
