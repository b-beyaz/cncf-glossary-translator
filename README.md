# CNCF Glossary Turkish Translator

An automated localization tool designed specifically for the [CNCF Glossary](https://glossary.cncf.io/). This tool ensures consistency in cloud-native terminology by leveraging a local glossary and the Anthropic Claude claude-sonnet-4-20250514 model.

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
# Edit .env and add your ANTHROPIC_API_KEY

# Run the web interface
streamlit run app.py
```

## Features

- **Glossary-Driven:** Strictly adheres to terms defined in your local glossary (`.csv` or `.xlsx` format)
- **AI-Powered Term Suggestions:** Automatically identifies new technical terms and suggests Turkish translations
- **Markdown Header Logic:** Automatically converts specific headers like "Problem it addresses" to their standard Turkish equivalents
- **Smart Link Conversion:** Transforms English internal links (`/en/`) to Turkish (`/tr/`) while translating the anchor text
- **Dynamic File Naming:** Parses the GitHub URL to name the output file accordingly (e.g., `multitenancy.md`)
- **YAML Frontmatter Support:** Translates metadata values (title, category, tags) while preserving the YAML keys
- **Web Interface:** User-friendly Streamlit interface for easy translation and glossary management

## Prerequisites
- Python 3.8+
- Authentication (choose one):
  - **Option 1**: Anthropic API Key (with access to Claude 3.5 Sonnet) - recommended for most users
  - **Option 2**: Google Cloud Platform account with Vertex AI enabled - for enterprise users

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

### 4. Setup environment variables
```bash
cp .env.example .env
```

Edit the `.env` file and configure authentication:

**For Direct Anthropic API** (most users):
```bash
ANTHROPIC_API_KEY=your_api_key_here
```

**For Google Cloud Vertex AI** (enterprise users):
```bash
ANTHROPIC_VERTEX_PROJECT_ID=your-gcp-project-id
CLOUD_ML_REGION=us-east5
```

### 5. (Optional) Configure model name

By default, the tool uses:
- **Direct API**: `claude-sonnet-4-20250514`
- **Vertex AI**: `claude-sonnet-4-5@20250929`

To use a different model, add to your `.env` file:
```bash
MODEL_NAME=your-model-name
```

### 6. Prepare your glossary file
The tool supports both `.csv` and `.xlsx` formats. Ensure your glossary file has two columns:
- `English` - English terms
- `Turkish` - Turkish translations

**Default location:** `glossary.csv` (can be configured via `GLOSSARY_PATH` in `.env`)

### Finding Available Models in Vertex AI

If you're using Google Cloud Vertex AI, you can find available Claude models:

**Using Claude Code (Easiest):**
If you're using Claude Code with Vertex AI configured, simply type `/model` in any Claude conversation to see all available models in your Vertex AI setup.

**Using Google Cloud Console:**
1. Visit the Vertex AI Model Garden for Anthropic:
   https://console.cloud.google.com/vertex-ai/model-garden/anthropic
2. Select your project
3. Browse available Claude models and their version identifiers

**Using Anthropic Documentation:**
- Check the official Vertex AI integration docs:
  https://docs.anthropic.com/en/api/claude-on-vertex-ai

**Common Vertex AI model identifiers:**
- `claude-sonnet-4-5@20250929` (recommended, default)
- `claude-3-5-sonnet@20240620`
- `claude-3-5-sonnet-v2@20241022`
- `claude-3-opus@20240229`
- `claude-3-sonnet@20240229`
- `claude-3-haiku@20240307`

**Important Notes:**
- Vertex AI model versions use the `@` format (e.g., `claude-sonnet-4-5@20250929`)
- Direct Anthropic API uses different identifiers (e.g., `claude-sonnet-4-20250514`)
- Model availability in Vertex AI may differ by region
- If you get a 404 error, verify the model is available in your region using the console link above

## Usage

### Option 1: Streamlit Web Interface (Recommended)
The easiest way to use the translator is through the Streamlit web interface:

```bash
streamlit run app.py
```

This will open a web browser with an interactive interface where you can:
- Enter GitHub URLs for translation
- View translation previews
- Manage glossary terms with AI suggestions
- Save translated files to the `outputs/` directory

### Option 2: Command Line Interface
For CLI usage, run the translator directly:

```bash
python utils/translator.py
```

When prompted:
1. Paste the GitHub "edit" or "blob" URL of the markdown file
2. The translated file will be saved in the `outputs/` directory

**Example URL formats:**
- `https://github.com/cncf/glossary/blob/main/content/en/api-gateway.md`
- `https://github.com/cncf/glossary/edit/main/content/en/service-mesh.md`

## Deactivating the Virtual Environment

When you're done, deactivate the virtual environment:
```bash
deactivate
```
