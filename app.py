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
st.set_page_config(page_title="Study-Buddy v5.3", page_icon="✈️", layout="wide")
translator = Translator()

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

# --- CSS ---
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

# --- SIDEBAR: HANGAR ---
with st.sidebar:
    st.header("🔧 Maintenance Hangar")
    input_text = st.text_area("Add Words (Bulk/Single):", placeholder="empirical, deviate, fluctuate...").strip().lower()
    
    if st.button("🚀 ADD TO DATABASE"):
        if input_text:
            words = [w.strip() for w in input_text.replace(',', '\n').split('\n') if w.strip()]
            db = load_db()
            progress = st.progress(0)
            for i, word in enumerate(words):
                try:
                    # Çeviri (Daha insani çeviri denemesi)
                    tr_res = translator.translate(word, src='en', dest='tr').text.lower()
                    # Eğer çeviri çok garipse (ampirik gibi), en azından sözlüğe bak
                    dict_url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
                    res = requests.get(dict_url, timeout=5)
                    w_type, example = "noun", "No example."
                    if res.status_code == 200:
                        data = res.json()[0]
                        types = [m['partOfSpeech'] for m in data['meanings']]
                        w_type = 'verb' if 'verb' in types else ('adjective' if 'adjective' in types else types[0])
                        for m in data['meanings']:
                            if m['partOfSpeech'] == w_type:
                                for d in m['definitions']:
                                    if 'example' in d:
                                        example = d['example']
                                        break
                    db[word] = {"anlam": tr_res, "tur": w_type, "ornek": example}
                except:
                    db[word] = {"anlam": word, "tur": "unknown", "ornek": "N/A"}
                progress.progress((i + 1) / len(words))
            save_db(db)
            st.success("Hangar updated!")
            st.rerun()
    st.info(f"Words in DB: {len(load_db())}")

# --- MENU ---
if st.session_state.mode == "menu":
    st.title("👨‍✈️ PILOT TEST CENTER")
    db = load_db()
    if db:
        all_types = sorted(list(set(v['tur'] for v in db.values())))
        selected = st.multiselect("Filter Type:", all_types, default=all_types)
        if st.button("🛫 START FLIGHT"):
            st.session_state.active_pool = {k: v for k, v in db.items() if v['tur'] in selected}
            st.session_state.mode = "flight"
            st.session_state.secilen = ""
            st.rerun()

# --- FLIGHT ---
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

    # GERİ BİLDİRİM VE O MEŞHUR BUTON
    if st.session_state.last_result:
        if "✅" in st.session_state.last_result:
            st.success(st.session_state.last_result)
        else:
            st.error(st.session_state.last_result)
            if st.button("⚠️ I actually knew this!"):
                st.session_state.dogru += 1
                st.session_state.yanlis -= 1
                if st.session_state.gecmis:
                    st.session_state.gecmis[-1]["Result"] = "✅ FIXED"
                st.session_state.last_result = "✅ Correction Applied!"
                st.rerun()

    with st.form(key='ans_form', clear_on_submit=True):
        ans = st.text_input("Meaning?")
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

    with st.expander("💡 HINT"):
        st.write(target.get('ornek'))
    if st.button("🏁 FINISH"):
        st.session_state.mode = "report"; st.rerun()

# --- REPORT ---
else:
    st.title("🛬 FLIGHT LOG")
    st.table(pd.DataFrame(st.session_state.gecmis))
    if st.button("🔄 MENU"):
        st.session_state.mode = "menu"; st.rerun()
