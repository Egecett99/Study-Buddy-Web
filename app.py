import sys
import requests
import streamlit as st
import json
import random
import io
import os
import pandas as pd
from gtts import gTTS
from googletrans import Translator

# --- SİSTEM AYARLARI ---
st.set_page_config(page_title="Study-Buddy v5.1", page_icon="✈️", layout="wide")
translator = Translator()

# --- VERİ YÖNETİMİ ---
DB_FILE = "vocabulary.json"

def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
        return {}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {}

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- CSS: PILOT UI ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #00e676; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; border: 1px solid #00e676; }
    .word-header { text-align: center; color: #00e676; font-size: 55px; font-weight: bold; margin-bottom: 0px; }
    .word-info { text-align: center; color: #888; margin-top: -10px; margin-bottom: 20px; font-style: italic; }
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

# --- SIDEBAR: KELİME EKLEME (HANGAR) ---
with st.sidebar:
    st.header("🔧 Maintenance Hangar")
    st.subheader("Add Words (Single or Bulk)")
    # İster "thrust" yaz, ister "thrust, wing, pilot" yaz
    input_text = st.text_area("Write words (use comma or new line):", placeholder="thrust, fuselage, drag...").strip().lower()
    
    if st.button("🚀 ADD TO DATABASE"):
        if input_text:
            words_to_process = [w.strip() for w in input_text.replace(',', '\n').split('\n') if w.strip()]
            db = load_db()
            progress_bar = st.progress(0)
            
            for i, word in enumerate(words_to_process):
                with st.spinner(f"Processing: {word}..."):
                    try:
                        if word not in db:
                            # AI Çeviri ve Tür Bulma
                            tr = translator.translate(word, src='en', dest='tr').text.lower()
                            dict_url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
                            res = requests.get(dict_url, timeout=5)
                            w_type, example = "noun", "No example found."
                            
                            if res.status_code == 200:
                                data = res.json()[0]
                                w_type = data['meanings'][0]['partOfSpeech']
                                for m in data['meanings']:
                                    for d in m['definitions']:
                                        if 'example' in d:
                                            example = d['example']
                                            break
                            db[word] = {"anlam": tr, "tur": w_type, "ornek": example, "kullanim": "Manual Entry"}
                    except:
                        db[word] = {"anlam": word, "tur": "unknown", "ornek": "Details not found.", "kullanim": "Error Recovery"}
                progress_bar.progress((i + 1) / len(words_to_process))
            
            save_db(db)
            st.success(f"Log: {len(words_to_process)} words processed!")
            st.rerun()
    
    st.divider()
    db_count = len(load_db())
    st.info(f"Hangar Status: {db_count} words")

# --- MENU EKRANI ---
if st.session_state.mode == "menu":
    st.title("👨‍✈️ PILOT TEST CENTER")
    db = load_db()
    if not db:
        st.warning("Database is empty! Use the sidebar to add words.")
    else:
        all_types = sorted(list(set(v['tur'] for v in db.values())))
        selected_type = st.multiselect("Filter by Type:", all_types, default=all_types)
        
        if st.button("🛫 START MISSION"):
            filtered_pool = {k: v for k, v in db.items() if v['tur'] in selected_type}
            if filtered_pool:
                st.session_state.active_pool = filtered_pool
                st.session_state.mode = "flight"
                st.session_state.secilen = ""
                st.rerun()

# --- FLIGHT (TEST) EKRANI ---
elif st.session_state.mode == "flight":
    if not st.session_state.secilen:
        st.session_state.secilen = random.choice(list(st.session_state.active_pool.keys()))
    
    target = st.session_state.active_pool[st.session_state.secilen]
    st.markdown(f"<div class='word-header'>{st.session_state.secilen.upper()}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='word-info'>({target['tur']})</div>", unsafe_allow_html=True)

    try:
        tts = gTTS(text=st.session_state.secilen, lang='en')
        b = io.BytesIO(); tts.write_to_fp(b); st.audio(b.getvalue())
    except: pass

    if st.session_state.last_result:
        if "✅" in st.session_state.last_result: st.success(st.session_state.last_result)
        else: st.error(st.session_state.last_result)

    with st.form(key='ans_form', clear_on_submit=True):
        ans = st.text_input("Turkish Meaning?")
        if st.form_submit_button("CHECK"):
            correct = target['anlam'].lower().strip()
            if ans.strip().lower() == correct:
                st.session_state.dogru += 1
                st.session_state.last_result = f"✅ SUCCESS! {st.session_state.secilen.upper()} = {correct.upper()}"
            else:
                st.session_state.yanlis += 1
                st.session_state.last_result = f"❌ FAIL! Correct: {correct.upper()}"
            st.session_state.gecmis.append({"Word": st.session_state.secilen.upper(), "Result": st.session_state.last_result})
            st.session_state.secilen = ""
            st.rerun()

    with st.expander("💡 HINT"):
        st.write(target.get('ornek'))
    if st.button("🏁 FINISH MISSION"):
        st.session_state.mode = "report"; st.rerun()

# --- RAPOR EKRANI ---
else:
    st.title("🛬 MISSION LOG")
    st.table(pd.DataFrame(st.session_state.gecmis))
    if st.button("🔄 BACK TO MENU"):
        st.session_state.mode = "menu"; st.rerun()
