import os
import requests
import pandas as pd
import anthropic
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

class CNCFTranslator:
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.glossary_path = os.getenv("GLOSSARY_PATH", "glossary.csv")
        
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found!")
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def load_local_glossary(self):
        try:
            if not os.path.exists(self.glossary_path):
                print(f"Warning: File {self.glossary_path} not found.")
                return ""
            
            if self.glossary_path.endswith('.xlsx'):
                df = pd.read_excel(self.glossary_path)
            else:
                df = pd.read_csv(self.glossary_path, encoding='utf-8-sig', sep=None, engine='python')
            
            print(f"Dictionary successfully loaded: {len(df)} words found.")
            return df.to_markdown(index=False)
        except Exception as e:
            print(f"Error while reading the dictionary: {e}")
            return ""

    def get_raw_url(self, url):
        return url.replace("https://github.com/", "https://raw.githubusercontent.com/").replace("/edit/", "/").replace("/blob/", "/")
    
    def get_filename_from_url(self, url):
        path = urlparse(url).path
        return os.path.basename(path)
    
    def translate(self, url):
        raw_url = self.get_raw_url(url)
        content_res = requests.get(raw_url)
        
        if content_res.status_code != 200:
            return f"Error: Source file could not be reached. (Code:{content_res.status_code})"

        source_text = content_res.text
        glossary = self.load_local_glossary()

        system_msg = f"""
        You are a professional CNCF Glossary translator specializing in Cloud Native technologies.
        
        RULES:
        1. GLOSSARY: Strictly adhere to the terminology in the provided glossary. Do not deviate from these Turkish equivalents:
        {glossary}
        
        2. LINKS: Convert [Text](/en/path/) to [Turkish Text](/tr/path/). 
           Crucial: Only translate the 'Text' part and change '/en/' to '/tr/'. Do not touch the rest of the slug.
           Example: [API Gateway](/en/api-gateway/) -> [API Geçidi](/tr/api-gateway/)
        
        3. FORMAT:
           - Headers: Always include a single space after '#' symbols (e.g., '## Header').
           - Spacing: Ensure exactly one blank line exists between paragraphs.
           - Frontmatter: Keep the YAML structure (between --- lines) intact. Translate the values for 'title', 'category', and 'tags' based on the glossary, but DO NOT translate the keys themselves.

        4. SPECIFIC HEADERS:
           - "Problem it addresses" -> "Hangi Sorunları Çözer"
           - "How it helps" -> "Nasıl Yardımcı Olur"
           - "Related terms" -> "Bağlantılı Terimler"
        
        5. LANGUAGE: Use a professional, technical, yet accessible Turkish tone suitable for the CNCF community.

        6. TRANSLATION POLICY:
           - NEVER leave technical concepts in English (like 'Policy as Code') unless they are international units or acronyms (like 'HTTP', 'gRPC', 'IP').
           - Avoid literal translations that sound robotic. Use professional DevOps terminology.

        Do not provide any introductory or concluding remarks. Return ONLY the translated markdown content.
        """

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514", 
                max_tokens=8192,
                system=system_msg,
                messages=[{"role": "user", "content": source_text}]
            )
            return response.content[0].text
        except Exception as e:
            return f"API Hatası: {e}"

if __name__ == "__main__":
    translator = CNCFTranslator()
    target_url = input("GitHub Çeviri Linki: ")
    
    filename = translator.get_filename_from_url(target_url)
    if not filename.endswith(".md"):
        filename = "translated_output.md"

    print(f"The process has started... Target file: {filename}")
    output = translator.translate(target_url)
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(output)
    
    print(f"\n--- TRANSLATION COMPLETE ---")
    print(f"The result was saved to the file '{filename}'.")