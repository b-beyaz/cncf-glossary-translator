import os
import re
import pandas as pd
import subprocess
import logging
import streamlit as st
from dotenv import load_dotenv
from git import Repo as GitRepo, InvalidGitRepositoryError
import tkinter as tk
from tkinter import filedialog


load_dotenv(override=True)

REPO_PATH = os.getenv("REPO_PATH", ".")
BASE_BRANCH = os.getenv("BASE_BRANCH", "dev-tr")
OUTPUT_DIR = os.getenv("OUTPUT_DIR")
curr_token = os.getenv("GITHUB_TOKEN")
curr_user = os.getenv("GITHUB_USER")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


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
    
def push_new_file_to_branch(REPO_PATH, branch, filepath, content, commit_msg):
    repo_name = "glossary"
    try:
        authenticated_url = f"https://{curr_token}@github.com/{curr_user}/{repo_name}.git"
        git(REPO_PATH, "checkout", branch)
        abs_path = os.path.join(REPO_PATH, filepath)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as fh:
            fh.write(content)
        logger.info(f"Dosya yazıldı: {abs_path}")

        git(REPO_PATH, "add", filepath)

        try:
            git(REPO_PATH, "commit", "--signoff", "-m", commit_msg)
            logger.info(f"Commit atıldı: {commit_msg}")
        except Exception as e:
            if "nothing to commit" in str(e).lower():
                logger.info("Commit atlanıldı: staged değişiklik yok.")
            else:
                raise
        git(REPO_PATH, "push", authenticated_url, branch)
        logger.info(f"Push successful → branch: {branch}")
        return True
    except Exception as e:
        logger.error(f"push_new_file_to_branch hatası: {str(e)}")
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

def choose_and_pull_branch(repo_path, branch_to_checkout):
    try:
        logger.info(f"The process has been initiated.: {repo_path}")
        try:
            logger.info("Changes are being stashed (if any)...")
            git(repo_path, "stash")
        except Exception as e:
            logger.info(f"Stash was skipped or not needed: {e}")
        logger.info(f"Branch is being changed. -> {branch_to_checkout}")
        git(repo_path, "checkout", branch_to_checkout)
        logger.info(f"'{branch_to_checkout}' Updates are being pulled...")
        output = git(repo_path, "pull", "origin", branch_to_checkout)

        logger.info(f"Pull result: {output}")
        return True

    except Exception as e:
        logger.error(f"Error during Git stream:: {str(e)}")
        raise Exception(f"An error occurred while updating the branch:: {str(e)}")


def get_filtered_repo_files(repo_path):
    all_files = []
    for root, dirs, files in os.walk(repo_path):
        if '.git' in dirs:
            dirs.remove('.git')  
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, repo_path).replace("\\", "/")
            all_files.append(rel_path)        
    return sorted(all_files)

def load_css(css_path: str) -> None:
    with open(css_path, "r", encoding="utf-8") as fh:
        st.markdown(f"<style>{fh.read()}</style>", unsafe_allow_html=True)

def get_repo(repo_path: str):
    try:
        return GitRepo(repo_path)
    except InvalidGitRepositoryError:
        return None

def build_file_tree(file_list: list[str]) -> dict:
    tree: dict = {}
    for f in file_list:
        parts = f.split("/")
        node = tree
        for part in parts:
            node = node.setdefault(part, {})
    return tree

def render_sidebar_tree(
    tree: dict,
    repo_path: str,
    current_path: str = "",
    depth: int = 0,
    content_key: str = "editor_content",
    file_key: str = "selected_file",
) -> None:
    for name, subtree in sorted(tree.items()):
        full_path = f"{current_path}/{name}".lstrip("/")
        padding = "  " * depth
        if subtree:  
            if depth == 0:
                with st.sidebar.expander(f"📁 {name}", expanded=True):
                    render_sidebar_tree(subtree, repo_path, full_path, depth + 1, content_key, file_key)
            else:
                st.sidebar.markdown(f"{padding}📂 **{name}**")
                render_sidebar_tree(subtree, repo_path, full_path, depth + 1, content_key, file_key)
        else:  # Dosya
            icon = "📝" if name.endswith(".md") else "📄"
            btn_key = f"{file_key}__{full_path}"
            if st.sidebar.button(
                f"{padding}{icon} {name}",
                key=btn_key,
                use_container_width=True,
            ):
                st.session_state[file_key] = full_path
                abs_path = os.path.join(repo_path, full_path)
                if os.path.isfile(abs_path):
                    with open(abs_path, "r", encoding="utf-8") as fh:
                        st.session_state[content_key] = fh.read()
                st.toast(f"Loaded: {name}", icon="📂")

def parse_translation_response(raw: str) -> tuple[str, list[tuple[str, str]]]:
    if "SUGGESTIONS:" not in raw:
        return raw.strip(), []
    main_part, suggestion_block = raw.split("SUGGESTIONS:", 1)
    suggestions: list[tuple[str, str]] = []
    for line in suggestion_block.strip().splitlines():
        if "|" in line:
            parts = line.split("|", 1)
            eng, tr = parts[0].strip(), parts[1].strip()
            if eng and eng.lower() not in ("english term", "---"):
                suggestions.append((eng, tr))
    return main_part.strip(), suggestions

def render_file_explorer(tree, current_path=""):
            for name, subtree in sorted(tree.items()):
                full_path = os.path.join(current_path, name).replace("\\", "/")
                if subtree:  
                    with st.expander(f"📁 {name}", expanded=False):
                        render_file_explorer(subtree, full_path)
                else:  
                    col1, col2 = st.columns([0.8, 0.2])
                    col1.text(f"📄 {name}")
                    if col2.button("Choose", key=f"select_{full_path}"):
                        st.session_state["branch_selected_file"] = full_path
                        abs_path = os.path.join(REPO_PATH, full_path)
                        with open(abs_path, "r", encoding="utf-8") as f:
                            st.session_state["branch_editor_content"] = f.read()
                        st.toast(f"File uploaded: {name}")
                        st.rerun()
def open_file_explorer_and_get_path(initial_dir="/mnt/c/glossary"):
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)

    file_path = filedialog.askopenfilename(
        initialdir=initial_dir,
        title="Select the file you want to edit.",
        filetypes=[("All Files", "*.*")] 
    )
    
    root.destroy()
    return file_path