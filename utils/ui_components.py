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