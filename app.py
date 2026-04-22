import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from utils.ui_components import StepManager
from utils.translator import CNCFTranslator
from utils.file_ops import (
    add_to_glossary,
    save_translation,
    create_branch,
    push_to_remote,
    push_new_file_to_branch,
    choose_and_pull_branch,
    load_css,
    get_repo,
    parse_translation_response,
    open_file_explorer_and_get_path
)

load_dotenv()

st.set_page_config(
    page_title="CNCF Glossary AI Suite",
    layout="wide",
    initial_sidebar_state="expanded",
)

REPO_PATH = os.getenv("REPO_PATH", ".")
BASE_BRANCH = os.getenv("BASE_BRANCH", "dev-tr")

load_css("styles/main.css")

@st.cache_resource
def get_translator():
    return CNCFTranslator()

@st.cache_resource
def cached_get_repo(path: str):
    return get_repo(path)

translator = get_translator()
repo = cached_get_repo(REPO_PATH)


with st.sidebar:
    with st.expander("📖 Glossary", expanded=False):
        if os.path.exists("glossary.csv"):
            st.dataframe(
                pd.read_csv("glossary.csv"),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.caption("No glossary file found yet.")

    st.divider()
    

    editing = st.session_state.get("branch_selected_file")
    if editing:
        st.divider()
        st.caption(f"🖊 Editing: `{editing}`")


tab_translate, tab_branch = st.tabs(
    ["🌐 Flow 1 — New Translation", "🌿 Flow 2 — Edit Existing Branch"]
)


with tab_translate:
    st.title("🚀 CNCF Glossary AI Translator")
    st.caption("Translate a Markdown file from GitHub, review the result, then push it as a new branch.")

    steps = StepManager()

    steps.render("Enter GitHub Markdown UR")
    
    url = st.text_input(
        label="URL",
        label_visibility="collapsed",
        placeholder="https://github.com/org/repo/blob/main/content/en/my-page.md",
    )

    if st.button("✨ Translate", type="primary", disabled=not url):
        with st.spinner("AI is translating and extracting terminology…"):
            try:
                raw = translator.translate(url)
                main_text, suggestions = parse_translation_response(raw)
                st.session_state.update(
                    {
                        "tab1_translation": main_text,
                        "tab1_suggestions": suggestions,
                        "tab1_filename": translator.get_filename_from_url(url),
                        "tab1_editor_content": main_text,
                    }
                )
            except Exception as exc:
                st.error(f"Translation failed: {exc}")

    if "tab1_translation" in st.session_state:
        st.divider()
        steps.render("Review & Edit Translation")
        
        left, right = st.columns([3, 1])

        with left:
            edited_text = st.text_area(
                "Markdown Editor",
                value=st.session_state.get("tab1_editor_content", st.session_state["tab1_translation"]),
                height=500,
                key="tab1_editor",
            )
            st.session_state["tab1_editor_content"] = edited_text

        with right:
            st.markdown("#### 🤖 AI Terminology")

            with st.expander("➕ Add Term Manually", expanded=False):
                m_eng = st.text_input("English", key="m_eng")
                m_tr = st.text_input("Turkish", key="m_tr")
                if st.button("Add to Glossary", key="manual_add"):
                    if m_eng and m_tr:
                        add_to_glossary(m_eng.strip(), m_tr.strip())
                        st.toast(f"Added: {m_eng}", icon="💾")
                    else:
                        st.warning("Fill both fields.")

            st.divider()
            suggestions = st.session_state.get("tab1_suggestions", [])
            if suggestions:
                st.caption(f"{len(suggestions)} term(s) suggested:")
                for eng, tr in suggestions:
                    with st.expander(f"💡 {eng}"):
                        final_tr = st.text_input("Translation", value=tr, key=f"sug_{eng}")
                        if st.button("Add to Glossary", key=f"add_{eng}"):
                            add_to_glossary(eng.strip(), final_tr.strip())
                            st.toast(f"✅ {eng} added.")
            else:
                st.info("No new terms suggested.")

        st.divider()
        steps.render("Create Branch & Push to Remote")

        filename = st.session_state.get("tab1_filename", "translation.md")
        clean_name = filename.replace(".md", "").replace(".", "-")

        col_branch, col_commit = st.columns(2)
        with col_branch:
            branch_name = st.text_input("Branch Name", value=f"tr-{clean_name}")
        with col_commit:
            commit_msg = st.text_input(
                "Commit Message",
                value=f"Add Turkish localization for {clean_name}",
            )

        if st.button("🚀 Push to Remote", type="primary"):
            with st.spinner("Creating branch and pushing…"):
                try:
                    st.session_state["tab1_translation"] = st.session_state["tab1_editor_content"]
                    create_branch(REPO_PATH, BASE_BRANCH, branch_name)
                    st.info(f"Branch created: `{branch_name}`")
                    save_translation(st.session_state["tab1_translation"], filename)
                    success = push_to_remote(
                        REPO_PATH=REPO_PATH,
                        new_branch=branch_name,
                        filename=filename,
                        commit=commit_msg,
                    )
                    if success:
                        st.success(f"Pushed to GitHub on branch `{branch_name}`! 🎉")
                        st.balloons()
                    else:
                        st.error("Push failed. Check your Git credentials or PAT.")
                except Exception as exc:
                    st.error(f"Git error: {exc}")

with tab_branch:
    st.title("🌿 Edit an Existing Branch")
    st.caption("Switch to a branch, edit or add a file, then commit & push.")

    if not repo:
        st.error(f"Cannot open Git repository at `{REPO_PATH}`. Check your REPO_PATH env variable.")
        st.stop()

    local_branches = [h.name for h in repo.heads]
    active_name = repo.active_branch.name

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
                for key in ("branch_selected_file", "branch_editor_content", "branch_mode"):
                    st.session_state.pop(key, None)
                st.success(f"Now on branch `{selected_branch}`.")
                st.rerun()
            except Exception as exc:
                st.error(f"Git error: {str(exc)}")

    st.markdown(
        f'Current branch: <span class="badge badge-green">⎇ {active_name}</span>',
        unsafe_allow_html=True,
    )

    st.divider()
    steps.render("What do you want to do?")

    mode = st.radio(
        "İşlem tipi",
        options=["✏️ Edit existing file", "➕ Add new file"],
        key="branch_mode",
        label_visibility="collapsed",
        horizontal=True,
    )

    st.divider()

    steps.render("File")

    target_filepath = None 

    if mode == "✏️ Edit existing file":
        if "selected_files_dict" not in st.session_state:
            st.session_state["selected_files_dict"] = {}

        if st.button("📁 Bilgisayarımdan Dosya Ekle"):
            path = open_file_explorer_and_get_path(REPO_PATH)
            if path:
                rel_path = os.path.relpath(path, REPO_PATH).replace("\\", "/")
                if rel_path not in st.session_state["selected_files_dict"]:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                        st.session_state["selected_files_dict"][rel_path] = content
                        st.toast(f"Listeye eklendi: {rel_path}")
                        st.rerun()
                else:
                    st.warning("bu dosya zaten listede ekli.")
        st.divider()

        if st.session_state["selected_files_dict"]:
            st.subheader("📝 Seçili Dosyaları Düzenle")
        
            for file_path in list(st.session_state["selected_files_dict"].keys()):
                with st.container(border=True):
                    col_title, col_del = st.columns([0.9, 0.1])
                    col_title.markdown(f"**📄 {file_path}**")
                
                    if col_del.button("❌", key=f"del_{file_path}"):
                        del st.session_state["selected_files_dict"][file_path]
                        st.rerun()

                    new_content = st.text_area(
                        "İçerik",
                        value=st.session_state["selected_files_dict"][file_path],
                        height=300,
                        key=f"editor_{file_path}"
                    )
                    st.session_state["selected_files_dict"][file_path] = new_content
    else:
        st.info("Henüz dosya seçilmedi. Yukarıdaki butonu kullanarak dosya ekleyin.")
        new_file_path = st.text_input(
            "File path",
            placeholder="content/tr/my-new-term.md",
            key="branch_new_filepath",
        )
        target_filepath = new_file_path.strip() if new_file_path else None
        if "branch_editor_content" not in st.session_state:
            st.session_state["branch_editor_content"] = ""
    st.divider()
    
    steps.render("Edit Content")
    
    branch_content = st.text_area(
        "File Content",
        value=st.session_state.get("branch_editor_content", ""),
        height=500,
        key="branch_editor",
        disabled=(not target_filepath),
        placeholder="" if target_filepath else "First select or specify a file above.",
    )
    if target_filepath:
        st.session_state["branch_editor_content"] = branch_content

    st.divider()

    steps.render("Commit & Push")

    commit_msg_branch = st.text_input(
        "Commit Message",
        placeholder="e.g. Fix: update Turkish translation for api-gateway.md",
        key="branch_commit_msg",
    )

    can_push = bool(target_filepath and commit_msg_branch.strip())

    if not can_push:
        if not target_filepath:
            st.caption("⚠️ Select a file or enter a new file path.")
        elif not commit_msg_branch.strip():
            st.caption("⚠️ Write a commit message.")

    if st.session_state.get("selected_files_dict") and st.button("🚀 Tüm Değişiklikleri Pushla"):
        success_count = 0
        branch_name = st.session_state.get("current_branch") # Mevcut branch adın
    
        for f_path, f_content in st.session_state["selected_files_dict"].items():
            try:
                push_new_file_to_branch(
                    REPO_PATH, 
                    branch_name, 
                    f_path, 
                    f_content, 
                    f"Update {f_path}"
                )
                success_count += 1
            except Exception as e:
                st.error(f"{f_path} pushlanırken hata oluştu: {e}")
        if success_count > 0:
            st.success(f"{success_count} dosya başarıyla güncellendi!")