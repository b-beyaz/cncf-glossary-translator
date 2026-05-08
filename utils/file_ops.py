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
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_NAME = os.getenv("GITHUB_NAME")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


import os

import os

import csv

def configure_git():
    email = os.getenv("GITHUB_EMAIL")
    name = os.getenv("GITHUB_NAME")
    subprocess.run(["git", "config", "--global", "user.email", email])
    subprocess.run(["git", "config", "--global", "user.name", name])

def add_to_glossary(english, turkish, notes="", file_path="glossary.csv"):
    try:
        if os.path.exists(file_path):
            with open(file_path, encoding='utf-8-sig') as f:
                for line in f:
                    if line.strip().lower().startswith(english.lower() + ","):
                        return False  
        file_exists = os.path.exists(file_path)
        with open(file_path, mode='a', encoding='utf-8-sig') as f:
            if not file_exists:
                f.write("English,Turkish,Notes\n")
            f.write(f"{english},{turkish},{notes}\n")
        return True
    except Exception as e:
        print(f"An error occurred while updating the dictionary: {e}")
        return False
    
def push_glossary_to_remote(commit_msg: str = "Update glossary.csv", glossary_repo_path: str = None):
    try:
        repo_path = glossary_repo_path or os.getenv("GLOSSARY_REPO_PATH", ".")
        logger.info(f"Glossary repo path: {repo_path}")

        repo = GitRepo(repo_path)
        logger.info(f"Active branch: {repo.active_branch.name}")
        
        glossary_full_path = os.path.join(repo_path, "glossary.csv")
        logger.info(f"glossary.csv exists: {os.path.exists(glossary_full_path)}")

        repo.index.add(["glossary.csv"])
       
        if not repo.index.diff("HEAD"):
            logger.warning("glossary.csv değişmemiş, commit yok.")
            return False
        
        repo.index.commit(commit_msg)
        logger.info("Commit yapıldı.")
        
        origin = repo.remotes.origin
        push_result = origin.push()
        logger.info(f"Push result: {push_result[0].summary}")
        return True
    except Exception as e:
        print(f"Glossary push failed: {e}")
        return False

def git(repo_path, *args):
    result = subprocess.run(
        ["git", *args],
        cwd=repo_path,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        error_msg = result.stderr.strip() or result.stdout.strip() or "unknown git error"
        logger.error(f"git {' '.join(args)} failed:\n  stdout: {result.stdout.strip()}\n  stderr: {result.stderr.strip()}\n  returncode: {result.returncode}")
        raise Exception(error_msg)
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
        authenticated_url = f"https://{GITHUB_TOKEN}@github.com/{GITHUB_NAME}/{repo_name}.git"
        output_dir = os.getenv("OUTPUT_DIR", "")
        rel_path = os.path.relpath(
            os.path.join(output_dir, filename),
            REPO_PATH
        )
        logger.info(f"git add path: {rel_path}")
        git(REPO_PATH, "checkout", new_branch)
        git(REPO_PATH, "add", rel_path)
        try:
            git(REPO_PATH, "commit", "--signoff", "-m", commit)
        except Exception as e:
            if "nothing to commit" in str(e).lower():
                logger.info("Nothing to commit.")
            else:
                raise
        git(REPO_PATH, "push", authenticated_url, new_branch, "--force")
        return True
    except Exception as e:
        raise Exception(f"Git Push Error: {str(e)}")
    
def push_new_file_to_branch(REPO_PATH, branch, filepath, content, commit_msg):
    repo_name = "glossary"
    try:
        authenticated_url = f"https://{GITHUB_TOKEN}@github.com/{GITHUB_NAME}/{repo_name}.git"
        git(REPO_PATH, "checkout", branch)
        abs_path = os.path.join(REPO_PATH, filepath)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as fh:
            fh.write(content)
        logger.info(f"File written: {abs_path}")
        git(REPO_PATH, "add", filepath)
        try:
            git(REPO_PATH, "commit", "--signoff", "-m", commit_msg)
            logger.info(f"Commit was rejected: {commit_msg}")
        except Exception as e:
            err_str = str(e).lower()
            if "nothing to commit" in err_str or "nothing added to commit" in err_str:
                logger.info("Commit skipped: no staged changes.")
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
        else:  
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
def open_file_explorer_and_get_path(initial_dir=""):
    return None  

def push_multiple_files_to_branch(REPO_PATH, branch, files_dict, commit_msg):
    repo_name = "glossary"
    try:
        authenticated_url = f"https://{GITHUB_TOKEN}@github.com/{GITHUB_NAME}/{repo_name}.git"
        git(REPO_PATH, "checkout", branch)
        for filepath, content in files_dict.items():
            logger.info(f"filepath value: '{filepath}'")
            abs_path = os.path.join(REPO_PATH, filepath)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, "w", encoding="utf-8") as fh:
                fh.write(content)
            logger.info(f"File written:: {abs_path}")
            git(REPO_PATH, "add", filepath)
        try:
            git(REPO_PATH, "commit", "--signoff", "-m", commit_msg)
            logger.info(f"Commit was rejected: {commit_msg}")
        except Exception as e:
            err_str = str(e).lower()
            if "nothing to commit" in err_str or "nothing added to commit" in err_str:
                logger.info("Commit skipped: no changes.")
            else:
                raise
        git(REPO_PATH, "push", authenticated_url, branch)
        logger.info(f"Push successful → branch: {branch}")
        return True
    except Exception as e:
        logger.error(f"push_multiple_files_to_branch hatası: {repr(e)}")
        raise Exception(f"Git Push Error: {str(e)}")