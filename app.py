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
st.set_page_config(page_title="Study-Buddy v5.0", page_icon="✈️", layout="wide")
translator = Translator()

# --- VERİ YÖNETİMİ (Kalıcı Dosya) ---
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
    st.subheader("Add New Word to Database")
    new_word = st.text_input("English Word:").strip().lower()
    
    if st.button("🚀 ADD TO DATABASE"):
        if new_word:
            with st.spinner(f"Analyzing {new_word}..."):
                try:
                    # AI Karşılık ve Tür Bulma
                    tr = translator.translate(new_word, src='en', dest='tr').text.lower()
                    dict_url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{new_word}"
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
                    
                    # Veritabanına Yazma
                    db = load_db()
                    db[new_word] = {"anlam": tr, "tur": w_type, "ornek": example, "kullanim": "Manual Entry"}
                    save_db(db)
                    st.success(f"Added: {new_word} -> {tr}")
                except Exception as e:
                    st.error(f"Error adding word: {e}")
        else:
            st.warning("Write a word first!")
    
    st.divider()
    db_count = len(load_db())
    st.info(f"Words in Database: {db_count}")

# --- MENU EKRANI ---
if st.session_state.mode == "menu":
    st.title("👨‍✈️ PILOT TEST CENTER")
    
    db = load_db()
    if not db:
        st.warning("Database is empty! Add words from the sidebar hangar first.")
    else:
        # Tür Filtreleme
        all_types = sorted(list(set(v['tur'] for v in db.values())))
        selected_type = st.multiselect("Filter by Type:", all_types, default=all_types)
        
        if st.button("🛫 START FLIGHT WITH DATABASE"):
            filtered_pool = {k: v for k, v in db.items() if v['tur'] in selected_type}
            if filtered_pool:
                st.session_state.active_pool = filtered_pool
                st.session_state.mode = "flight"
                st.session_state.secilen = ""
                st.rerun()
            else:
                st.error("No words found for the selected types!")

# --- FLIGHT (TEST) EKRANI ---
elif st.session_state.mode == "flight":
    if not st.session_state.secilen:
        st.session_state.secilen = random.choice(list(st.session_state.active_pool.keys()))
    
    target = st.session_state.active_pool[st.session_state.secilen]
    st.markdown(f"<div class='word-header'>{st.session_state.secilen.upper()}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='word-info'>({target['tur']}) | Source: {target.get('kullanim')}</div>", unsafe_allow_html=True)

    # Ses
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
            if st.button("⚠️ I knew this!"):
                st.session_state.dogru += 1
                st.session_state.yanlis -= 1
                st.session_state.gecmis[-1]["Result"] = "✅ Fixed"
                st.session_state.last_result = "✅ Corrected!"
                st.rerun()

    with st.form(key='ans_form', clear_on_submit=True):
        ans = st.text_input("What is the Turkish meaning?")
        if st.form_submit_button("CHECK"):
            correct = target['anlam'].lower().strip()
            if ans.strip().lower() == correct:
                st.session_state.dogru += 1
                st.session_state.last_result = f"✅ CORRECT! {st.session_state.secilen.upper()} = {correct.upper()}"
            else:
                st.session_state.yanlis += 1
                st.session_state.last_result = f"❌ WRONG! Correct: {correct.upper()}"
            
            st.session_state.gecmis.append({"Word": st.session_state.secilen.upper(), "Result": st.session_state.last_result})
            st.session_state.secilen = "" 
            st.rerun()

    with st.expander("💡 HINT (Sentence)"):
        st.write(target.get('ornek', 'No sentence found.'))

    if st.button("🏁 FINISH MISSION"):
        st.session_state.mode = "report"
        st.rerun()

# --- RAPOR EKRANI ---
else:
    st.title("🛬 FLIGHT LOG")
    st.write(f"📊 **Final Score:** {st.session_state.dogru} / {st.session_state.yanlis}")
    st.table(pd.DataFrame(st.session_state.gecmis))
    if st.button("🔄 BACK TO MENU"):
        st.session_state.mode = "menu"
        st.session_state.secilen = ""
        st.session_state.gecmis = []
        st.session_state.dogru = 0
        st.session_state.yanlis = 0
        st.session_state.last_result = None
        st.rerun()
