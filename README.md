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
- Anthropic API Key (with access to Claude 3.5 Sonnet)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/b-beyaz/cncf-glossary-translator.git
   cd cncf-glossary-translator
   ```
2. Install dependencies:
   pip install -r requirements.txt

3. Setup environment variables:
   cp .env.example .env
   Edit the .env file and add your ANTHROPIC_API_KEY.

Usage
1. Prepare your glossary in glossary.xlsx (ensure it has 'English' and 'Turkish' columns).

2. Run the script:
  python3 translator.py

3. Paste the GitHub "edit" or "blob" URL when prompted.

4. The translated file will be generated in the same directory.
