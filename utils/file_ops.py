import os
import subprocess
import logging
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from git import Repo as GitRepo, InvalidGitRepositoryError

load_dotenv(override=True)

REPO_PATH = os.getenv("REPO_PATH", ".")
OUTPUT_DIR = os.getenv("OUTPUT_DIR")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_NAME = os.getenv("GITHUB_NAME")
GITHUB_USER = os.getenv("GITHUB_USER")
GITHUB_EMAIL = os.getenv("GITHUB_EMAIL")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ── Git configuration ──────────────────────────────────────────────────────────

def configure_git():
    subprocess.run(["git", "config", "--global", "user.email", GITHUB_EMAIL])
    subprocess.run(["git", "config", "--global", "user.name", GITHUB_NAME])
    credentials = f"https://{GITHUB_USER}:{GITHUB_TOKEN}@github.com"
    with open(os.path.expanduser("~/.git-credentials"), "w") as fh:
        fh.write(credentials)


configure_git()


# ── Glossary helpers ───────────────────────────────────────────────────────────

def add_to_glossary(
    english: str,
    translated: str,
    file_path: str,
    notes: str = "",
) -> bool:
    try:
        if os.path.exists(file_path):
            with open(file_path, encoding="utf-8-sig") as fh:
                for line in fh:
                    if line.strip().lower().startswith(english.lower() + ","):
                        return False

        file_exists = os.path.exists(file_path)
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        with open(file_path, mode="a", encoding="utf-8-sig") as fh:
            if not file_exists:
                fh.write("English,Translation,Notes\n")
            fh.write(f"{english},{translated},{notes}\n")
        return True

    except Exception as exc:
        logger.error(f"Error updating glossary: {exc}")
        return False


def read_glossary(file_path: str = "") -> str:
    if not os.path.exists(file_path):
        return ""
    try:
        df = pd.read_csv(file_path, encoding="utf-8-sig")
        return df.to_markdown(index=False)
    except Exception as exc:
        logger.error(f"Error reading glossary: {exc}")
        return ""


def push_glossary_to_remote(
    commit_msg: str = "Update glossary",
    glossary_repo_path: str | None = None,
    glossary_filename: str = "",  
) -> tuple[bool, str]:
    try:
        repo_path = glossary_repo_path or os.getenv("GLOSSARY_REPO_PATH", ".")
        logger.info(f"Glossary repo: {repo_path}")

        repo = GitRepo(repo_path)
        logger.info(f"Active branch: {repo.active_branch.name}")

        full_path = os.path.join(repo_path, glossary_filename)
        if not os.path.exists(full_path):
            msg = f"Glossary file not found: {full_path}"
            logger.error(msg)
            return False, msg

        rel_path = os.path.relpath(full_path, repo_path)
        logger.info(f"Staging: {rel_path}")
        repo.index.add([rel_path])

        staged_files = [item.a_path for item in repo.index.diff("HEAD")]
        norm_rel = rel_path.replace("\\", "/")
        if norm_rel not in [p.replace("\\", "/") for p in staged_files]:
            msg = f"{rel_path} unchanged — nothing to commit."
            logger.warning(msg)
            return False, msg

        repo.index.commit(commit_msg)
        logger.info("Committed.")

        push_result = repo.remotes.origin.push()
        logger.info(f"Push result: {push_result[0].summary}")
        return True, ""

    except Exception as exc:
        msg = str(exc)
        logger.error(f"Glossary push failed: {msg}")
        return False, msg


# ── Low-level git wrapper ──────────────────────────────────────────────────────

def git(repo_path: str, *args) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        msg = result.stderr.strip() or result.stdout.strip() or "unknown git error"
        logger.error(
            f"git {' '.join(args)} failed:\n"
            f"  stdout: {result.stdout.strip()}\n"
            f"  stderr: {result.stderr.strip()}\n"
            f"  returncode: {result.returncode}"
        )
        raise Exception(msg)
    return result.stdout.strip()


# ── Branch & push helpers ──────────────────────────────────────────────────────

def create_branch(repo_path: str, base_branch: str, new_branch: str) -> None:
    git(repo_path, "stash")
    git(repo_path, "checkout", base_branch)
    git(repo_path, "pull", "origin", base_branch)
    git(repo_path, "checkout", "-b", new_branch)
    logger.info(f"Branch '{new_branch}' created from '{base_branch}'.")


def push_to_remote(
    REPO_PATH: str,
    new_branch: str,
    filename: str,
    commit: str,
    repo_name: str = "glossary",
) -> bool:
    try:
        remote_url = f"https://github.com/{GITHUB_NAME}/{repo_name}.git"
        output_dir = os.getenv("OUTPUT_DIR", "")
        rel_path = os.path.relpath(
            os.path.join(output_dir, filename), REPO_PATH
        )
        logger.info(f"git add path: {rel_path}")

        git(REPO_PATH, "checkout", new_branch)
        git(REPO_PATH, "add", rel_path)
        try:
            git(REPO_PATH, "commit", "--signoff", "-m", commit)
        except Exception as exc:
            if "nothing to commit" not in str(exc).lower():
                raise
        git(REPO_PATH, "push", remote_url, new_branch, "--force")
        return True

    except Exception as exc:
        raise Exception(f"Git Push Error: {exc}")


def push_new_file_to_branch(
    REPO_PATH: str,
    branch: str,
    filepath: str,
    content: str,
    commit_msg: str,
    repo_name: str = "glossary",
) -> bool:
    try:
        remote_url = f"https://github.com/{GITHUB_NAME}/{repo_name}.git"
        git(REPO_PATH, "checkout", branch)

        abs_path = os.path.join(REPO_PATH, filepath)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as fh:
            fh.write(content)
        logger.info(f"Written: {abs_path}")
        git(REPO_PATH, "add", filepath)
        try:
            git(REPO_PATH, "commit", "--signoff", "-m", commit_msg)
        except Exception as exc:
            err = str(exc).lower()
            if "nothing to commit" not in err and "nothing added" not in err:
                raise
        git(REPO_PATH, "push", remote_url, branch)
        logger.info(f"Pushed → branch: {branch}")
        return True
    except Exception as exc:
        logger.error(f"push_new_file_to_branch error: {exc}")
        raise Exception(f"Git Push Error: {exc}")

def push_multiple_files_to_branch(
    REPO_PATH: str,
    branch: str,
    files_dict: dict[str, str],
    commit_msg: str,
    repo_name: str = "glossary",
) -> bool:
    try:
        remote_url = f"https://github.com/{GITHUB_NAME}/{repo_name}.git"
        git(REPO_PATH, "checkout", branch)

        for filepath, content in files_dict.items():
            abs_path = os.path.join(REPO_PATH, filepath)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, "w", encoding="utf-8") as fh:
                fh.write(content)
            logger.info(f"Written: {abs_path}")
            git(REPO_PATH, "add", filepath)
        try:
            git(REPO_PATH, "commit", "--signoff", "-m", commit_msg)
        except Exception as exc:
            err = str(exc).lower()
            if "nothing to commit" not in err and "nothing added" not in err:
                raise
        git(REPO_PATH, "push", remote_url, branch)
        logger.info(f"Pushed {len(files_dict)} file(s) → branch: {branch}")
        return True
    except Exception as exc:
        logger.error(f"push_multiple_files_to_branch error: {repr(exc)}")
        raise Exception(f"Git Push Error: {exc}")
    
def choose_and_pull_branch(repo_path: str, branch: str) -> bool:
    try:
        try:
            git(repo_path, "stash")
        except Exception as exc:
            logger.info(f"Stash skipped: {exc}")
        git(repo_path, "checkout", branch)
        output = git(repo_path, "pull", "origin", branch)
        logger.info(f"Pull result: {output}")
        return True

    except Exception as exc:
        logger.error(f"Git error: {exc}")
        raise Exception(f"Error updating branch: {exc}")


# ── File helpers ───────────────────────────────────────────────────────────────

def save_translation(content: str, filename: str) -> str | None:
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    if not filename.endswith(".md"):
        filename += ".md"
    target = os.path.join(OUTPUT_DIR, filename)
    try:
        with open(target, "w", encoding="utf-8") as fh:
            fh.write(content)
        return target
    except Exception as exc:
        logger.error(f"Error saving translation: {exc}")
        return None

def get_filtered_repo_files(repo_path: str) -> list[str]:
    all_files = []
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d != ".git"]
        for file in files:
            full = os.path.join(root, file)
            rel = os.path.relpath(full, repo_path).replace("\\", "/")
            all_files.append(rel)
    return sorted(all_files)

# ── Repo helpers ───────────────────────────────────────────────────────────────

def get_repo(repo_path: str):
    try:
        return GitRepo(repo_path)
    except InvalidGitRepositoryError:
        return None

# ── UI helpers ─────────────────────────────────────────────────────────────────

def load_css(css_path: str) -> None:
    with open(css_path, "r", encoding="utf-8") as fh:
        st.markdown(f"<style>{fh.read()}</style>", unsafe_allow_html=True)

def build_file_tree(file_list: list[str]) -> dict:
    tree: dict = {}
    for f in file_list:
        node = tree
        for part in f.split("/"):
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
                    render_sidebar_tree(
                        subtree, repo_path, full_path, depth + 1, content_key, file_key
                    )
            else:
                st.sidebar.markdown(f"{padding}📂 **{name}**")
                render_sidebar_tree(
                    subtree, repo_path, full_path, depth + 1, content_key, file_key
                )
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

def render_file_explorer(tree: dict, current_path: str = "") -> None:
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
                with open(abs_path, "r", encoding="utf-8") as fh:
                    st.session_state["branch_editor_content"] = fh.read()
                st.toast(f"File uploaded: {name}")
                st.rerun()

def parse_translation_response(raw: str) -> tuple[str, list[tuple[str, str]]]:
    if "SUGGESTIONS:" not in raw:
        return raw.strip(), []
    main_part, suggestion_block = raw.split("SUGGESTIONS:", 1)
    suggestions: list[tuple[str, str]] = []
    for line in suggestion_block.strip().splitlines():
        if "|" in line:
            eng, tr = line.split("|", 1)
            eng, tr = eng.strip(), tr.strip()
            if eng and eng.lower() not in ("english term", "---"):
                suggestions.append((eng, tr))
    return main_part.strip(), suggestions

def open_file_explorer_and_get_path(initial_dir: str = "") -> None:
    return None