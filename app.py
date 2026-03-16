import sys
import requests
import streamlit as st
import json
import random
import io
import pandas as pd
from gtts import gTTS
from googletrans import Translator

# --- SİSTEM AYARLARI ---
st.set_page_config(page_title="Aerospace Mastery v6.0", page_icon="✈️", layout="wide")
translator = Translator()

# Veri Kaynağı (A1-C2 Seviyeli 5000+ Kelime)
DATA_URL = "https://raw.githubusercontent.com/freetooland/english-vocabulary-data/main/data.json"

@st.cache_data
def load_web_data():
    try:
        response = requests.get(DATA_URL, timeout=10)
        if response.status_code == 200:
            return response.json()
        return {}
    except:
        return {}

# --- CSS: PILOT UI ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #00e676; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; border: 1px solid #00e676; height: 3em; background-color: transparent; color: #00e676; }
    .stButton>button:hover { background-color: #00e676; color: #0e1117; }
    .word-header { text-align: center; color: #00e676; font-size: 60px; font-weight: bold; margin-bottom: 0px; text-shadow: 2px 2px 10px #00e676; }
    .word-info { text-align: center; color: #888; margin-top: -10px; margin-bottom: 20px; font-style: italic; font-size: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE ---
if 'mode' not in st.session_state:
    st.session_state.mode = "menu"
    st.session_state.active_pool = {}
    st.session_state.secilen = ""
    st.session_state.dogru = 0
    st.session_state.yanlis = 0
    st.session_state.gecmis = []
    st.session_state.last_result = None

# --- AI ANALYZER (CUSTOM LIST İÇİN) ---
def process_user_list(text):
    words = [w.strip() for w in text.replace(',', '\n').split('\n') if w.strip()]
    processed = {}
    bar = st.progress(0)
    for i, word in enumerate(words):
        try:
            tr = translator.translate(word, src='en', dest='tr').text.lower()
            processed[word.lower()] = {"anlam": tr, "tur": "custom", "seviye": "User", "ornek": f"Practice word: {word}"}
        except:
            processed[word.lower()] = {"anlam": word, "tur": "N/A", "seviye": "User", "ornek": "Translation error."}
        bar.progress((i + 1) / len(words))
    return processed

# --- ANA MENÜ ---
if st.session_state.mode == "menu":
    st.title("👨‍✈️ AEROSPACE PILOT SELECTION")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📦 Global Database (A1-C2)")
        all_data = load_web_data()
        
        if all_data:
            levels = sorted(list(set(val['seviye'] for val in all_data.values())))
            selected_level = st.selectbox("Select Flight Level:", levels)
            
            if st.button("🚀 START MISSION"):
                # Seçilen seviyedeki kelimeleri havuzla
                st.session_state.active_pool = {k: v for k, v in all_data.items() if v['seviye'] == selected_level}
                st.session_state.mode = "flight"
                st.session_state.secilen = ""
                st.rerun()
        else:
            st.error("Connection lost! Check DATA_URL.")

    with col2:
        st.subheader("📝 Custom Cargo (List)")
        user_input = st.text_area("Paste your words:", placeholder="thrust, fuselage, cockpit...", height=150)
        if st.button("🛠️ CREATE CUSTOM FLIGHT"):
            if user_input:
                with st.spinner("AI Loading Cargo..."):
                    st.session_state.active_pool = process_user_list(user_input)
                    st.session_state.mode = "flight"
                    st.session_state.secilen = ""
                    st.rerun()

# --- UÇUŞ (TEST) EKRANI ---
elif st.session_state.mode == "flight":
    if not st.session_state.active_pool:
        st.session_state.mode = "menu"
        st.rerun()

    if not st.session_state.secilen:
        st.session_state.secilen = random.choice(list(st.session_state.active_pool.keys()))
    
    target = st.session_state.active_pool[st.session_state.secilen]
    
    st.markdown(f"<div class='word-header'>{st.session_state.secilen.upper()}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='word-info'>[{target.get('seviye', 'A2')}] - {target.get('tur', 'noun')}</div>", unsafe_allow_html=True)

    # Seslendirme
    try:
        tts = gTTS(text=st.session_state.secilen, lang='en')
        b = io.BytesIO(); tts.write_to_fp(b)
        st.audio(b.getvalue())
    except: pass

    # Geri Bildirim
    if st.session_state.last_result:
        if "✅" in st.session_state.last_result: st.success(st.session_state.last_result)
        else:
            st.error(st.session_state.last_result)
            if st.button("⚠️ I knew this! (Correct It)"):
                st.session_state.dogru += 1
                st.session_state.yanlis -= 1
                st.session_state.gecmis[-1]["Status"] = "✅ Corrected"
                st.session_state.last_result = "✅ Log updated!"
                st.rerun()

    with st.form(key='flight_form', clear_on_submit=True):
        ans = st.text_input("Enter Turkish Meaning:")
        submit = st.form_submit_button("CHECK DATA")
        
        if submit:
            correct_ans = target['anlam'].lower().strip()
            user_ans = ans.strip().lower()
            
            if user_ans == correct_ans:
                st.session_state.dogru += 1
                st.session_state.last_result = f"✅ TARGET HIT! {st.session_state.secilen.upper()} = {correct_ans.upper()}"
            else:
                st.session_state.yanlis += 1
                st.session_state.last_result = f"❌ MISSION FAILED! Correct: {correct_ans.upper()}"
            
            st.session_state.gecmis.append({"Word": st.session_state.secilen, "Status": st.session_state.last_result})
            st.session_state.secilen = ""
            st.rerun()

    with st.expander("💡 RECON (Hint)"):
        st.write(target.get('ornek', 'No example available.'))

    if st.button("🏁 END MISSION"):
        st.session_state.mode = "report"
        st.rerun()

# --- RAPOR EKRANI ---
else:
    st.title("🛬 MISSION REPORT")
    colA, colB = st.columns(2)
    colA.metric("SUCCESSFUL HITS", st.session_state.dogru)
    colB.metric("MISSED TARGETS", st.session_state.yanlis)
    
    st.table(pd.DataFrame(st.session_state.gecmis))
    
    if st.button("🔄 RETURN TO HANGAR"):
        st.session_state.mode = "menu"
        st.session_state.dogru = 0
        st.session_state.yanlis = 0
        st.session_state.gecmis = []
        st.session_state.secilen = ""
        st.session_state.last_result = None
        st.rerun()
