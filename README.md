# CNCF Glossary Turkish Translator
An automated localization tool designed specifically for the [CNCF Glossary](https://glossary.cncf.io/). This tool ensures consistency in cloud-native terminology by leveraging a local glossary and the Anthropic Claude claude-sonnet-4-20250514 model.

## Features
- **Glossary-Driven:** Strictly adheres to terms defined in your local `glossary.xlsx`.
- **Markdown Header Logic:** Automatically converts specific headers like "Problem it addresses" to their standard Turkish equivalents.
- **Smart Link Conversion:** Transforms English internal links (`/en/`) to Turkish (`/tr/`) while translating the anchor text.
- **Dynamic File Naming:** Parses the GitHub URL to name the output file accordingly (e.g., `multitenancy.md`).
- **YAML Frontmatter Support:** Translates metadata values (title, category, tags) while preserving the YAML keys.

## Prerequisites
- Python 3.8+
- Authentication (choose one):
  - **Option 1**: Anthropic API Key (with access to Claude 3.5 Sonnet) - recommended for most users
  - **Option 2**: Google Cloud Platform account with Vertex AI enabled - for enterprise users

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/b-beyaz/cncf-glossary-translator.git
   cd cncf-glossary-translator
   ```
2. Install dependencies:
    ```
   pip install -r requirements.txt
     ```
3. Setup environment variables:
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

4. (Optional) Configure model name:

   By default, the tool uses:
   - **Direct API**: `claude-sonnet-4-20250514`
   - **Vertex AI**:  `claude-sonnet-4-5@20250929`

   To use a different model, add to your `.env` file:
   ```bash
   MODEL_NAME=your-model-name
   ```

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

**Important Notes:**
- Vertex AI model versions use the `@` format (e.g., `claude-sonnet-4-5@20250929`)
- Direct Anthropic API uses different identifiers (e.g., `claude-sonnet-4-20250514`)
- Model availability in Vertex AI may differ by region
- If you get a 404 error, verify the model is available in your region using the console link above

## Usage
1. Prepare your glossary in glossary.xlsx (ensure it has 'English' and 'Turkish' columns).

2. Run the script:
  ```
  python3 translator.py
 ```

4. Paste the GitHub "edit" or "blob" URL when prompted.

5. The translated file will be generated in the same directory.
