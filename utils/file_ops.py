import os
import pandas as pd

def add_to_glossary(english, turkish, file_path="glossary.csv"):
    new_data = pd.DataFrame([[english, turkish]], columns=["English", "Turkish"])
    try:
        if os.path.exists(file_path):
            new_data.to_csv(file_path, mode='a', header=False, index=False, encoding='utf-8-sig')
        else:
            new_data.to_csv(file_path, index=False, encoding='utf-8-sig')
        return True
    except Exception as e:
        print(f"An error occurred while updating the dictionary: {e}")
        return False

def save_translation(content, filename):
    output_dir = "outputs"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    if not filename.endswith(".md"):
        filename += ".md"
    target_path = os.path.join(output_dir, filename)
    try:
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)
        return target_path
    except Exception as e:
        print(f"An error occurred while saving the file: {e}")
        return None

def read_glossary(file_path="glossary.csv"):
    if not os.path.exists(file_path):
        return ""
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        return df.to_markdown(index=False)
    except Exception as e:
        print(f"Error while reading the dictionary: {e}")
        return ""