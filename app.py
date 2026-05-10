import io
import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from config.languages import LANGUAGES, LanguageConfig, available_languages, get_language
from utils.file_ops import (
    add_to_glossary,
    choose_and_pull_branch,
    create_branch,
    get_repo,
    load_css,
    push_glossary_to_remote,
    push_multiple_files_to_branch,
    push_to_remote,
    save_translation,
    configure_git,
    read_glossary,
)
from utils.logger import logger
from utils.translator import CNCFTranslator
from utils.ui_components import StepManager, render_file_uploader

load_dotenv()
configure_git()

logger.info("App starting…")

st.set_page_config(
    page_title="CNCF Glossary AI Suite",
    layout="wide",
    initial_sidebar_state="expanded",
)

REPO_PATH = os.getenv("REPO_PATH", ".")
load_css("styles/main.css")


# ── Cached resources ───────────────────────────────────────────────────────────

@st.cache_resource
def get_translator():
    return CNCFTranslator()


@st.cache_resource
def cached_get_repo(path: str):
    return get_repo(path)


translator = get_translator()

try:
    repo = cached_get_repo(REPO_PATH)
except Exception as exc:
    logger.error(f"Repo could not be opened: {exc}")
    repo = None


# ── Language selector ──────────────────────────────────────────────────────────

def _lang_options() -> tuple[list[str], list[str]]:
    pairs = available_languages()
    return [p[0] for p in pairs], [p[1] for p in pairs]


def current_lang() -> LanguageConfig:
    return get_language(st.session_state.get("selected_lang_code", "tr"))


# ── SIDEBAR ────────────────────────────────────────────────────────────────────

with st.sidebar:

    # ── Language picker ────────────────────────────────────────────────────────
    st.subheader("🌍 Target Language")
    codes, labels = _lang_options()
    env_lang = os.getenv("LANGUAGE", "tr")
    default_idx = codes.index(env_lang) if env_lang in codes else 0

    selected_idx = st.selectbox(
        "Language",
        options=range(len(codes)),
        format_func=lambda i: labels[i],
        index=default_idx,
        key="_lang_selectbox",
        label_visibility="collapsed",
    )

    # Dil değişince eski çeviri & suggestions'ı temizle
    new_lang_code = codes[selected_idx]
    if st.session_state.get("selected_lang_code") != new_lang_code:
        for key in ("tab1_suggestions", "tab1_translation",
                    "tab1_editor_content", "tab1_filename"):
            st.session_state.pop(key, None)

    st.session_state["selected_lang_code"] = new_lang_code
    lang = current_lang()
    st.caption(f"Branch base: `{lang.base_branch}` · Glossary: `{lang.glossary_path}`")

    st.divider()

    # ── Glossary viewer ────────────────────────────────────────────────────────
    with st.expander("📖 Glossary", expanded=True):
        if os.path.exists(lang.glossary_path):
            st.dataframe(
                pd.read_csv(lang.glossary_path, on_bad_lines="skip"),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.caption(f"No glossary file found for {lang.name} yet.")

        # ── Term suggestions ───────────────────────────────────────────────────
        if st.session_state.get("tab1_suggestions"):
            st.divider()
            st.subheader("💡 Proposed New Terms")
            st.caption("Edit and select terms to add to the glossary:")

            raw = st.session_state["tab1_suggestions"].strip()

            # Satır satır parse et — pd.read_csv kullanma,
            # AI formatı tutarsız olabilir (---, boş satır, farklı header vb.)
            rows = []
            for line in raw.splitlines():
                line = line.strip()
                # Boş satır veya yalnızca tire/pipe/boşluk içeren ayraç satırı
                if not line or not line.replace("|", "").replace("-", "").replace(" ", ""):
                    continue
                if "|" not in line:
                    continue
                parts = [p.strip() for p in line.split("|", 1)]
                if len(parts) != 2:
                    continue
                eng, tr = parts
                if eng.lower() in ("english term", "english", "term"):
                    continue
                if eng and tr:
                    rows.append({"English Term": eng, lang.name: tr})

            df_suggestions = pd.DataFrame(rows)

            if not df_suggestions.empty:
                df_edit = df_suggestions.copy()
                df_edit.insert(0, "Add", False)

                edited_df = st.data_editor(
                    df_edit,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Add": st.column_config.CheckboxColumn(width="small"),
                        "English Term": st.column_config.TextColumn(width="medium"),
                        lang.name: st.column_config.TextColumn(width="medium"),
                    },
                )
                selected = edited_df[edited_df["Add"] == True]

                col_add, col_clear = st.columns(2)

                with col_add:
                    if st.button("✅ Add Selected", disabled=selected.empty):
                        added_count = 0
                        for _, row in selected.iterrows():
                            added = add_to_glossary(
                                row["English Term"],
                                row[lang.name],
                                "auto-suggested",
                                file_path=lang.glossary_path,
                            )
                            if added:
                                added_count += 1
                            logger.info(
                                f"{'Added' if added else 'Already exists'}: "
                                f"{row['English Term']}"
                            )
                        st.toast(f"{added_count} term(s) added!", icon="✅")

                        # Ekleme sonrası otomatik remote sync
                        with st.spinner("Syncing glossary to remote…"):
                            push_ok, push_msg = push_glossary_to_remote(
                                commit_msg=f"Add suggested terms [{lang.code}]",
                                glossary_repo_path=lang.glossary_repo_path,
                                glossary_filename=lang.glossary_path,
                            )
                            if push_ok:
                                st.toast("Glossary synced to remote!", icon="☁️")
                            else:
                                st.toast(
                                    f"Local save OK. Remote: {push_msg}", icon="⚠️"
                                )
                        st.rerun()

                with col_clear:
                    if st.button("🗑️ Clear"):
                        st.session_state.pop("tab1_suggestions", None)
                        st.rerun()
            else:
                st.caption("No suggestions could be parsed from the last translation.")

    st.divider()

    # ── Manuel terim ekleme ────────────────────────────────────────────────────
    with st.expander(f"➕ Add Term ({lang.native_name})", expanded=False):
        m_eng = st.text_input("English", key="m_eng")
        m_tr = st.text_input(lang.name, key="m_tr")
        m_notes = st.text_input("Notes (optional)", key="m_notes")
        if st.button("Add to Glossary", key="manual_add"):
            if m_eng and m_tr:
                added = add_to_glossary(
                    m_eng.strip(), m_tr.strip(), m_notes.strip(),
                    file_path=lang.glossary_path,
                )
                if added:
                    st.toast(f"Added: {m_eng}", icon="💾")
                    st.rerun()
                else:
                    st.warning(f"'{m_eng}' already exists in glossary.")
            else:
                st.warning("Fill both fields.")

    st.divider()

    # ── Glossary push ──────────────────────────────────────────────────────────
    commit_msg_glossary = st.text_input(
        "Glossary commit message",
        value=f"Update {lang.glossary_path}",
        key="glossary_commit_msg",
    )
    if st.button("☁️ Sync Glossary — Push to Remote", type="secondary"):
        with st.spinner("Pushing glossary…"):
            logger.info(f"Glossary repo path: {lang.glossary_repo_path}")
            logger.info(f"Glossary file: {lang.glossary_path}")
            push_ok, push_msg = push_glossary_to_remote(
                commit_msg=commit_msg_glossary,
                glossary_repo_path=lang.glossary_repo_path,
                glossary_filename=lang.glossary_path,
            )
            if push_ok:
                st.success("Glossary pushed! ✅")
            else:
                st.error(f"Push failed: {push_msg}")

    editing = st.session_state.get("branch_selected_file")
    if editing:
        st.divider()
        st.caption(f"🖊 Editing: `{editing}`")


# ── Navigation ─────────────────────────────────────────────────────────────────

if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = "🌐 Flow 1 — New Translation"

options = ["🌐 Flow 1 — New Translation", "🌿 Flow 2 — Edit Existing Branch"]
st.radio(
    "Navigation",
    options=options,
    index=options.index(st.session_state["active_tab"])
    if st.session_state["active_tab"] in options
    else 0,
    key="active_tab",
    horizontal=True,
    label_visibility="collapsed",
)

lang = current_lang()


# ── FLOW 1 — New Translation ───────────────────────────────────────────────────

if "Flow 1" in st.session_state["active_tab"]:
    st.title(f"🚀 CNCF Glossary AI Translator → {lang.native_name}")
    st.caption("Enter the GitHub URL, translate it, and grow your glossary with AI.")

    steps = StepManager()
    steps.render("Enter GitHub Markdown URL")

    url = st.text_input(
        label="URL",
        label_visibility="collapsed",
        placeholder="https://github.com/.../file.md",
    )

    if st.button("✨ Translate", type="primary", disabled=not url):
        with st.spinner(f"Translating to {lang.name}…"):
            try:
                translation, suggestions = translator.translate(url, lang=lang)
                st.session_state.update(
                    {
                        "tab1_translation": translation,
                        "tab1_filename": translator.get_filename_from_url(url),
                        "tab1_editor_content": translation,
                        "tab1_suggestions": suggestions,
                    }
                )
                logger.info(
                    f"Suggestions: '{suggestions[:100] if suggestions else 'NONE'}'"
                )
                st.rerun()
            except Exception as exc:
                logger.error(f"Translation failed: {exc}")
                st.error(f"Translation failed: {exc}")

    if "tab1_translation" in st.session_state:
        st.divider()
        steps.render("Review & Edit Translation")

        edited_text = st.text_area(
            "Markdown Editor",
            value=st.session_state.get(
                "tab1_editor_content", st.session_state["tab1_translation"]
            ),
            height=500,
            key="tab1_editor",
        )
        st.session_state["tab1_editor_content"] = edited_text

        st.divider()
        steps.render("Create Branch & Push to Remote")

        filename = st.session_state.get("tab1_filename", "translation.md")
        clean_name = filename.replace(".md", "").replace(".", "-")

        col_branch, col_commit = st.columns(2)
        with col_branch:
            branch_name = st.text_input(
                "Branch Name",
                value=f"{lang.code}-{clean_name}",
            )
        with col_commit:
            commit_msg = st.text_input(
                "Commit Message",
                value=f"Add {lang.name} localization for {clean_name}",
            )

        if st.button("🚀 Push to Remote", type="primary"):
            with st.spinner("Creating branch and pushing…"):
                try:
                    st.session_state["tab1_translation"] = st.session_state[
                        "tab1_editor_content"
                    ]
                    create_branch(REPO_PATH, lang.base_branch, branch_name)
                    st.info(f"Branch created: `{branch_name}`")
                    save_translation(st.session_state["tab1_translation"], filename)
                    success = push_to_remote(
                        REPO_PATH=REPO_PATH,
                        new_branch=branch_name,
                        filename=filename,
                        commit=commit_msg,
                    )
                    if success:
                        logger.info(f"Pushed to branch: {branch_name}")
                        st.success(f"Pushed to GitHub on `{branch_name}`! 🎉")
                        st.balloons()
                    else:
                        st.error("Push failed. Check Git credentials or PAT.")
                except Exception as exc:
                    logger.error(f"Git error: {exc}")
                    st.error(f"Git error: {exc}")


# ── FLOW 2 — Edit Existing Branch ─────────────────────────────────────────────

else:
    st.title("🌿 Edit an Existing Branch")
    st.caption("Switch to a branch, edit or add a file, then commit & push.")

    if not repo:
        st.error(
            f"Cannot open Git repository at `{REPO_PATH}`. "
            "Check your REPO_PATH env variable."
        )
        st.stop()

    local_branches = [h.name for h in repo.heads]
    active_name = repo.active_branch.name
    st.session_state["current_branch"] = active_name

    steps = StepManager()
    steps.render("Select Branch")

    if "branch_selectbox" not in st.session_state:
        st.session_state["branch_selectbox"] = active_name

    col_sel, col_btn = st.columns([3, 1])
    with col_sel:
        selected_branch = st.selectbox(
            "Local branches",
            options=local_branches,
            key="branch_selectbox",
            label_visibility="collapsed",
        )
    with col_btn:
        switch_btn = st.button(
            "Switch & Pull",
            type="primary",
            disabled=(selected_branch == active_name),
        )

    if switch_btn:
        with st.spinner(f"Checking out `{selected_branch}` and pulling…"):
            try:
                choose_and_pull_branch(REPO_PATH, selected_branch)
                cached_get_repo.clear()
                for key in (
                    "branch_selected_file",
                    "branch_editor_content",
                    "branch_mode",
                    "selected_files_dict",
                ):
                    st.session_state.pop(key, None)
                st.success(f"Now on branch `{selected_branch}`.")
                st.rerun()
            except Exception as exc:
                st.error(f"Git error: {exc}")

    st.markdown(
        f'Current branch: <span class="badge badge-green">⎇ {active_name}</span>',
        unsafe_allow_html=True,
    )

    st.divider()
    steps.render("File")

    if "selected_files_dict" not in st.session_state:
        st.session_state["selected_files_dict"] = {}

    st.session_state["selected_files_dict"] = render_file_uploader(
        st.session_state["selected_files_dict"]
    )

    st.divider()

    if st.session_state["selected_files_dict"]:
        st.subheader("📝 Edit Selected Files")

        for file_path in list(st.session_state["selected_files_dict"].keys()):
            with st.container(border=True):
                col_title, col_del = st.columns([0.9, 0.1])
                col_title.markdown(f"**📄 {file_path}**")

                if col_del.button("❌", key=f"del_{file_path}"):
                    del st.session_state["selected_files_dict"][file_path]
                    st.rerun()

                new_content = st.text_area(
                    "Contents",
                    value=st.session_state["selected_files_dict"][file_path],
                    height=300,
                    key=f"editor_{file_path}",
                )
                st.session_state["selected_files_dict"][file_path] = new_content

        st.divider()
        steps.render("Commit & Push")

        commit_msg_edit = st.text_input(
            "Commit Message",
            placeholder=f"Fix: update {lang.name} translation for api-gateway.md",
            key="branch_commit_msg_edit",
        )

        if not commit_msg_edit.strip():
            st.caption("⚠️ Please enter a commit message.")

        if st.button(
            "🚀 Push all changes",
            type="primary",
            disabled=not commit_msg_edit.strip(),
        ):
            branch_name = st.session_state.get("current_branch", active_name)
            with st.spinner(f"Pushing to '{branch_name}'…"):
                try:
                    push_multiple_files_to_branch(
                        REPO_PATH,
                        branch_name,
                        st.session_state["selected_files_dict"],
                        commit_msg_edit.strip(),
                    )
                    n = len(st.session_state["selected_files_dict"])
                    st.success(f"{n} file(s) pushed to `{branch_name}`! 🎉")
                    st.balloons()
                except Exception as exc:
                    st.error(f"Git error: {exc}")
    else:
        st.info("No files selected yet. Add a file using the button above.")