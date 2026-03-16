import sys
try:
    import cgi
except ImportError:
    import legacy_cgi as cgi
    sys.modules["cgi"] = cgi
import streamlit as st
import streamlit as st
import json
import random
import os
from gtts import gTTS
import io
import pandas as pd
from googletrans import Translator

# --- SİSTEM AYARLARI ---
st.set_page_config(page_title="Study-Buddy AI", page_icon="🚀", layout="wide")
translator = Translator()

# --- CSS: PILOT UI ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #00e676; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; }
    .report-card { background-color: #161b22; padding: 20px; border-radius: 15px; border: 1px solid #00e676; }
    h1 { text-align: center; color: #00e676; }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION INITIALIZATION ---
if 'user_pool' not in st.session_state:
    st.session_state.user_pool = {}
    st.session_state.dogru = 0
    st.session_state.yanlis = 0
    st.session_state.secilen = ""
    st.session_state.last_result = None
    st.session_state.gecmis = []
    st.session_state.app_mode = "setup" # setup veya flight

# --- AI DATA GENERATOR ---
def process_raw_list(text):
    words = [w.strip() for w in text.replace(',', '\n').split('\n') if w.strip()]
    processed = {}
    progress_bar = st.progress(0)
    
    for i, word in enumerate(words):
        try:
            # Otomatik Anlam ve Bilgi Çekme
            tr_meaning = translator.translate(word, src='en', dest='tr').text.lower()
            processed[word.lower()] = {
                "anlam": tr_meaning,
                "tur": "detected",
                "kullanim": "",
                "ornek": f"AI generated sentence for {word}.",
                "oncelik": 100
            }
        except:
            continue
        progress_bar.progress((i + 1) / len(words))
    return processed

# --- SETUP SCREEN ---
if st.session_state.app_mode == "setup":
    st.title("🛫 FLIGHT PREPARATION")
    st.subheader("Kelime Listeni Yapıştır (Virgül veya Alt Alta)")
    
    raw_input = st.text_area("Örn: propulsion, velocity, thrust...", height=150)
    
    if st.button("🚀 ANALİZ ET VE UÇUŞA BAŞLA"):
        if raw_input:
            with st.spinner("AI Kelimeleri Analiz Ediyor..."):
                st.session_state.user_pool = process_raw_list(raw_input)
                st.session_state.app_mode = "flight"
                st.rerun()
        else:
            st.error("Lütfen en az bir kelime yaz!")

# --- FLIGHT SCREEN (THE TEST) ---
else:
    if not st.session_state.secilen:
        st.session_state.secilen = random.choice(list(st.session_state.user_pool.keys()))

    st.title("✈️ IN-FLIGHT TEST")
    
    # Kelime Kartı
    word_data = st.session_state.user_pool[st.session_state.secilen]
    st.markdown(f"<h1 style='font-size: 60px;'>{st.session_state.secilen.upper()}</h1>", unsafe_allow_html=True)
    
    # Audio
    tts = gTTS(text=st.session_state.secilen, lang='en')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    st.audio(fp.getvalue(), format="audio/mpeg")

    # Form
    with st.form(key='answer_form', clear_on_submit=True):
        ans = st.text_input("Türkçe Anlamı:")
        submit = st.form_submit_button("KONTROL ET")
        
        if submit:
            correct = word_data['anlam']
            if ans.strip().lower() == correct:
                st.session_state.dogru += 1
                st.session_state.last_result = f"✅ DOĞRU! ({correct})"
                st.balloons()
            else:
                st.session_state.yanlis += 1
                st.session_state.last_result = f"❌ YANLIŞ! Doğrusu: {correct.upper()}"
            
            st.session_state.gecmis.append({"Kelime": st.session_state.secilen, "Sonuç": st.session_state.last_result})
            st.session_state.secilen = random.choice(list(st.session_state.user_pool.keys()))
            st.rerun()

    if st.session_state.last_result:
        st.info(st.session_state.last_result)

    if st.button("🏁 UÇUŞU BİTİR VE RAPORU GÖR"):
        st.session_state.app_mode = "report"
        st.rerun()

# --- REPORT SCREEN ---
if st.session_state.app_mode == "report":
    st.title("🛬 FLIGHT LOG")
    df = pd.DataFrame(st.session_state.gecmis)
    st.table(df)
    if st.button("🔄 YENİ LİSTE EKLE"):
        st.session_state.app_mode = "setup"
        st.session_state.gecmis = []
        st.session_state.user_pool = {}
        st.rerun()
