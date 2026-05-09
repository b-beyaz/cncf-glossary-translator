import streamlit as st
import os
from utils.file_ops import get_filtered_repo_files

class StepManager:
    def __init__(self):
        self.current_step = 1

    def render(self, title):
        html = f"""
        <div class="step-header">
            <div class="step-num">{self.current_step}</div>
            <div class="step-title">{title}</div>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)
        self.current_step += 1 
    
def render_file_uploader(selected_files_dict: dict) -> dict:
    repo_path = os.getenv("REPO_PATH", ".")
    all_files = get_filtered_repo_files(repo_path)
    
    # Dosyayı repo'dan seç
    selected = st.selectbox(
        "📁 Select file from repo",
        options=[""] + all_files,
        key="flow2_file_select",
        label_visibility="collapsed",
        placeholder="Select a file..."
    )
    
    if st.button("➕ Add to Editor", key="flow2_add_btn", disabled=not selected):
        if selected not in selected_files_dict:
            abs_path = os.path.join(repo_path, selected)
            with open(abs_path, "r", encoding="utf-8") as f:
                content = f.read()
            selected_files_dict[selected] = content
            st.toast(f"Added: {selected}")
        else:
            st.warning("Already in the list.")
    
    return selected_files_dict