import streamlit as st
import pandas as pd
import re
from utils.translator import CNCFTranslator
from utils.file_ops import add_to_glossary, save_translation


st.set_page_config(page_title="CNCF Glossary AI Suite", layout="wide")

@st.cache_resource
def get_translator():
    return CNCFTranslator()

translator = get_translator()

st.title("🚀 CNCF Glossary AI Translator")
st.markdown("Enter the GitHub URL, translate it, and develop your dictionary with AI.")

with st.sidebar:
    st.header("Dictionary Status")
    if st.checkbox("Show Current Dictionary"):
        df = pd.read_csv("glossary.csv")
        st.dataframe(df, use_container_width=True)

url = st.text_input("GitHub Markdown URL:", placeholder="https://github.com/.../file.md")

if st.button("Start Translation"):
    if url:
        with st.spinner("AI does the translation and analyzes the terms...."):
            try:
                raw_response = translator.translate(url)
                
                main_text = ""
                clean_suggestions = []

                if "SUGGESTIONS:" in raw_response:
                    parts = raw_response.split("SUGGESTIONS:", 1)
                    main_text = parts[0].strip()
                    suggestion_block = parts[1].strip()
                    
                    lines = suggestion_block.split('\n')
                    for line in lines:
                        if '|' in line:
                            sub_parts = line.split('|')
                            if len(sub_parts) == 2:
                                eng = sub_parts[0].strip()
                                tr = sub_parts[1].strip()
                                if eng and eng.lower() not in ["english term", "---"]:
                                    clean_suggestions.append((eng, tr))
                else:
                    main_text = raw_response.strip()
                    clean_suggestions = []
                st.session_state['current_translation'] = main_text
                st.session_state['suggestions'] = clean_suggestions
                st.session_state['filename'] = translator.get_filename_from_url(url)
                
            except Exception as e:
                st.error(f"An error occurred during translation:: {e}")
    else:
        st.warning("Please enter a valid URL..")

if 'current_translation' in st.session_state:
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Translation Preview")
        st.text_area("Markdown Output", st.session_state['current_translation'], height=500)
        
        if st.button("📥 Save it locally"):
            path = save_translation(st.session_state['current_translation'], st.session_state['filename'])
            st.success(f"The file has been successfully saved: {path}")

    with col2:
        st.subheader("🤖 Terminology Management")
        
        with st.expander("➕ Add New Term (Manual)", expanded=False):
            manual_eng = st.text_input("English Term:", key="manual_eng")
            manual_tr = st.text_input("Turkish Equivalent:", key="manual_tr")
            if st.button("Manually Add to Dictionary"):
                if manual_eng and manual_tr:
                    add_to_glossary(manual_eng.strip(), manual_tr.strip())
                    st.toast(f"'{manual_eng}' added manually!", icon="💾")
                else:
                    st.error("Please fill in both fields.")

        st.divider()

        st.info("Terms identified by AI:")
        
        suggestions = st.session_state.get('suggestions', [])
        
        if suggestions and len(suggestions) > 0:
            for eng, tr in suggestions:
                if not eng or eng.lower() in ["english term", "---"]:
                    continue
                    
                with st.expander(f"Öneri: {eng}"):
                    final_tr = st.text_input("Çeviri:", value=tr.strip(), key=f"input_{eng}")
                    if st.button(f"Sözlüğe Ekle", key=f"btn_{eng}"):
                        add_to_glossary(eng.strip(), final_tr.strip())
                        st.toast(f"'{eng}' sözlüğe eklendi!", icon="✅")
        else:
            st.success("Yeni bir terim önerisi bulunamadı. Sözlük kapsamı yeterli görünüyor.")
