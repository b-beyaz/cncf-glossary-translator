import streamlit as st

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
        uploaded_file = st.file_uploader(
            "📁 Add File From My Computer",
            type=["md", "txt"],
            key="flow2_uploader"
        )
        if uploaded_file is not None:
            rel_path = uploaded_file.name
            if rel_path not in selected_files_dict:
                content = uploaded_file.read().decode("utf-8")
                selected_files_dict[rel_path] = content
                st.toast(f"Added: {rel_path}")
            else:
                st.warning("This file is already in the list.")
        return selected_files_dict