import os
import requests
import pandas as pd
import anthropic
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

class CNCFTranslator:
    def __init__(self):
        self.glossary_path = os.getenv("GLOSSARY_PATH", "glossary.csv")

        # Detect authentication mode: Vertex AI or Direct API
        vertex_project_id = os.getenv("ANTHROPIC_VERTEX_PROJECT_ID")

        if vertex_project_id:
            # Use Vertex AI / Google Cloud authentication
            region = os.getenv("CLOUD_ML_REGION", "us-east5")
            print(f"Initializing with Vertex AI (project: {vertex_project_id}, region: {region})")
            self.client = anthropic.AnthropicVertex(
                project_id=vertex_project_id,
                region=region
            )
            # Default model for Vertex AI
            self.model = os.getenv("MODEL_NAME", "claude-sonnet-4-5@20250929")
        else:
            # Use direct Anthropic API authentication
            self.api_key = os.getenv("ANTHROPIC_API_KEY")
            if not self.api_key:
                raise ValueError(
                    "Authentication required: Set either ANTHROPIC_API_KEY "
                    "or ANTHROPIC_VERTEX_PROJECT_ID environment variable"
                )
            print("Initializing with direct Anthropic API")
            self.client = anthropic.Anthropic(api_key=self.api_key)
            # Default model for Direct API
            self.model = os.getenv("MODEL_NAME", "claude-sonnet-4-20250514")

        print(f"Using model: {self.model}")

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
           - Frontmatter: Keep the YAML structure (between --- lines) intact. 
             For 'title', 'category', and 'tags' values, follow this PRIORITY:
             1. Check the local glossary first. Use the exact term if found.
             2. If a term is NOT in the glossary, translate it into Turkish according to CNCF/IT industry standards (e.g., 'storage' -> 'depolama', 'networking' -> 'ağ oluşturma'). 
             3. DO NOT translate the keys (title:, category:, tags:), only the values.
             4. Ensure tags remain comma-separated and technically accurate.
        4. SPECIFIC HEADERS:
           - "Problem it addresses" -> "Hangi Sorunları Çözer"
           - "How it helps" -> "Nasıl Yardımcı Olur"
           - "Related terms" -> "Bağlantılı Terimler"
        
        5. LANGUAGE: Use a professional, technical, yet accessible Turkish tone suitable for the CNCF community.

        6. TRANSLATION POLICY:
           - NEVER leave technical concepts in English (like 'Policy as Code') unless they are international units or acronyms (like 'HTTP', 'gRPC', 'IP').
           - Avoid literal translations that sound robotic. Use professional DevOps terminology.
        
        7.TERM SUGGESTIONS 
            Analyze the source text for technical terms that are NOT in the glossary.
        
            RULES FOR SUGGESTIONS:
            - ONLY suggest technical, cloud-native, or DevOps-specific terms (e.g., "Service Mesh", "Sidecar", "Reconciliation").
            - DO NOT suggest terms already present in the provided glossary.
            - FORMAT: You must provide suggestions at the VERY END of your response.
            - OUTPUT FORMAT: 
                SUGGESTIONS:
                English Term,Recommended Turkish Translation
        Do not provide any introductory or concluding remarks. Return ONLY the translated markdown content.
        """

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=8192,
                system=system_msg,
                messages=[{"role": "user", "content": source_text}]
            )
            return response.content[0].text
        except Exception as e:
            return f"API Hatası: {e}"
    def add_to_glossary(english, turkish, file_path="glossary.csv"):
        new_data = pd.DataFrame([[english, turkish]], columns=["English", "Turkish"])
    
        if os.path.exists(file_path):
            new_data.to_csv(file_path, mode='a', header=False, index=False, encoding='utf-8-sig')
        else:
            new_data.to_csv(file_path, index=False, encoding='utf-8-sig')

    def save_translation(content, filename):
        if not os.path.exists("outputs"):
            os.makedirs("outputs")
        target_path = os.path.join("outputs", filename)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)
        return target_path
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
