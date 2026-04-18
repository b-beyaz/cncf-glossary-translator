import os
import re
import pandas as pd
import subprocess

from git import Repo
from dotenv import load_dotenv

load_dotenv(override=True)

REPO_PATH = os.getenv("REPO_PATH", ".") # Mevcut dizin varsayılan
BASE_BRANCH = os.getenv("BASE_BRANCH", "dev-tr")
OUTPUT_DIR = os.getenv("OUTPUT_DIR")
curr_token = os.getenv("GITHUB_TOKEN")
curr_user = os.getenv("GITHUB_USER")

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

def git(repo_path, *args):
    result = subprocess.run(
        ["git", *args],
        cwd=repo_path,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise Exception(result.stderr.strip())
    return result.stdout.strip()

def create_branch(REPO_PATH, BASE_BRANCH, new_branch):
    git(REPO_PATH, "stash")
    git(REPO_PATH, "checkout", BASE_BRANCH)
    git(REPO_PATH, "pull", "origin", BASE_BRANCH)
    git(REPO_PATH, "checkout", "-b", new_branch)
    print(f"✓ '{new_branch}' created based on '{BASE_BRANCH}'")

def push_to_remote(REPO_PATH, new_branch, filename, commit):
    repo_name = "glossary" 

    try:
        authenticated_url = f"https://{curr_token}@github.com/{curr_user}/{repo_name}.git"
        git(REPO_PATH, "checkout", new_branch)
        output_dir = os.getenv("OUTPUT_DIR", ".")
        file_to_add = os.path.join(output_dir, filename)
        git(REPO_PATH, "add", file_to_add)
        
        try:
            git(REPO_PATH, "commit", "--signoff", "-m", commit)
        except:
            print("No changes were found to commit.")
        git(REPO_PATH, "push", authenticated_url, new_branch, "--force")
        
        return True
    except Exception as e:
        raise Exception(f"Git Push Error: {str(e)}")

def save_translation(content, filename):
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    if not filename.endswith(".md"):
        filename += ".md"
    target_path = os.path.join(OUTPUT_DIR, filename)
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