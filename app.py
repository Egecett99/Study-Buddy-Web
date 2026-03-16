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
st.set_page_config(page_title="Study-Buddy v4.2", page_icon="✈️")
translator = Translator()

# Python 3.14 CGI Yaması
try:
    import cgi
except ImportError:
    try:
        import legacy_cgi as cgi
        sys.modules["cgi"] = cgi
    except ImportError:
        pass

# --- CSS: PILOT UI ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #00e676; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; border: 1px solid #00e676; height: 3em; }
    .word-header { text-align: center; color: #00e676; font-size: 55px; font-weight: bold; margin-bottom: 0px; }
    .word-info { text-align: center; color: #888; margin-top: -10px; margin-bottom: 20px; font-style: italic; }
    </style>
    """, unsafe_allow_html=True)

# --- AI KELİME ANALİZCİSİ ---
def process_user_list(text):
    words = [w.strip() for w in text.replace(',', '\n').split('\n') if w.strip()]
    processed = {}
    bar = st.progress(0)
    for i, word in enumerate(words):
        try:
            tr = translator.translate(word, src='en', dest='tr').text.lower()
            dict_url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
            response = requests.get(dict_url, timeout=5)
            w_type, example = "noun", f"Master the word '{word}'."
            if response.status_code == 200:
                data = response.json()[0]
                w_type = data['meanings'][0]['partOfSpeech']
                for m in data['meanings']:
                    for d in m['definitions']:
                        if 'example' in d:
                            example = d['example']
                            break
                    if "Master the" not in example: break
            processed[word.lower()] = {"anlam": tr, "tur": w_type, "ornek": example, "kullanim": "Custom Entry"}
        except:
            processed[word.lower()] = {"anlam": word, "tur": "unknown", "ornek": "Details not found.", "kullanim": "N/A"}
        bar.progress((i + 1) / len(words))
    return processed

# --- SESSION STATE INITIALIZATION ---
if 'mode' not in st.session_state:
    st.session_state.mode = "menu"
    st.session_state.active_pool = {}
    st.session_state.secilen = ""
    st.session_state.dogru = 0
    st.session_state.yanlis = 0
    st.session_state.gecmis = []
    st.session_state.last_result = None

# --- MENU EKRANI ---
if st.session_state.mode == "menu":
    st.title("👨‍✈️ PILOT SELECTION MENU")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📦 Main Database")
        if st.button("START WITH FIXED POOL"):
            try:
                with open("kelime_veritabani.json", "r", encoding="utf-8") as f:
                    # Hafızayı temizle ve yeni havuzu yükle
                    st.session_state.active_pool = json.load(f)
                    st.session_state.mode = "flight"
                    st.session_state.secilen = "" # Önceki seçimi sıfırla
                    st.rerun()
            except Exception as e:
                st.error(f"Database error: {e}")
                
    with col2:
        st.subheader("📝 Custom List")
        user_input = st.text_area("Paste words:", placeholder="undertake, velocity...", key="user_input_area")
        if st.button("CREATE CUSTOM SESSION"):
            if user_input:
                with st.spinner("AI Analyzing..."):
                    # Hafızayı temizle ve kullanıcının havuzunu yükle
                    st.session_state.active_pool = process_user_list(user_input)
                    st.session_state.mode = "flight"
                    st.session_state.secilen = "" # Önceki seçimi sıfırla
                    st.rerun()
            else: st.warning("Please enter some words first!")

# --- FLIGHT (TEST) EKRANI ---
elif st.session_state.mode == "flight":
    # Havuz boşsa menüye at
    if not st.session_state.active_pool:
        st.session_state.mode = "menu"
        st.rerun()

    # Yeni kelime seçimi
    if not st.session_state.secilen:
        st.session_state.secilen = random.choice(list(st.session_state.active_pool.keys()))
    
    target = st.session_state.active_pool[st.session_state.secilen]
    
    st.markdown(f"<div class='word-header'>{st.session_state.secilen.upper()}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='word-info'>({target['tur']}) | {target.get('kullanim', 'Standard')}</div>", unsafe_allow_html=True)

    # Ses Motoru
    tts = gTTS(text=st.session_state.secilen, lang='en')
    b = io.BytesIO(); tts.write_to_fp(b)
    st.audio(b.getvalue())

    # Geri Bildirim ve Düzeltme
    if st.session_state.last_result:
        if "✅" in st.session_state.last_result:
            st.success(st.session_state.last_result)
        else:
            st.error(st.session_state.last_result)
            if st.button("⚠️ I actually knew this!"):
                st.session_state.dogru += 1
                st.session_state.yanlis -= 1
                st.session_state.gecmis[-1]["Result"] = "✅ DÜZELTİLDİ"
                st.session_state.last_result = "✅ Correction Applied!"
                st.rerun()

    with st.form(key='ans_form', clear_on_submit=True):
        ans = st.text_input("Meaning?")
        if st.form_submit_button("CHECK"):
            correct = target['anlam'].lower()
            if ans.strip().lower() == correct:
                st.session_state.dogru += 1
                st.session_state.last_result = f"✅ CORRECT! {st.session_state.secilen.upper()} = {correct.upper()}"
            else:
                st.session_state.yanlis += 1
                st.session_state.last_result = f"❌ WRONG! Correct: {correct.upper()}"
            
            st.session_state.gecmis.append({"Word": st.session_state.secilen.upper(), "Result": st.session_state.last_result})
            st.session_state.secilen = "" # Yeni kelime seçilmesi için sıfırla
            st.rerun()

    with st.expander("💡 HINT (Sentence)"):
        st.write(target.get('ornek', 'No sentence found.'))

    if st.button("🏁 FINISH FLIGHT"):
        st.session_state.mode = "report"
        st.rerun()

# --- RAPOR EKRANI ---
else:
    st.title("🛬 FLIGHT LOG")
    st.write(f"📊 **Score:** {st.session_state.dogru} / {st.session_state.yanlis}")
    st.table(pd.DataFrame(st.session_state.gecmis))
    if st.button("🔄 BACK TO MENU"):
        # HER ŞEYİ SIFIRLA
        st.session_state.mode = "menu"
        st.session_state.secilen = ""
        st.session_state.gecmis = []
        st.session_state.dogru = 0
        st.session_state.yanlis = 0
        st.session_state.last_result = None
        st.session_state.active_pool = {}
        st.rerun()
