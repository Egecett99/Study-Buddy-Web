import sys
import requests
import streamlit as st
import json
import random
import io
import pandas as pd
from gtts import gTTS
from googletrans import Translator

# --- CGI PATCH FOR PYTHON 3.14 ---
try:
    import cgi
except ImportError:
    try:
        import legacy_cgi as cgi
        sys.modules["cgi"] = cgi
    except ImportError:
        pass

# --- INITIAL SETUP ---
st.set_page_config(page_title="Study-Buddy v5.0", page_icon="🚀", layout="centered")
translator = Translator()

# --- CSS: PILOT UI ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #00e676; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; border: 1px solid #00e676; height: 3em; }
    .word-header { text-align: center; color: #00e676; font-size: 50px; font-weight: bold; margin-bottom: 5px; }
    .word-info { text-align: center; color: #888; margin-bottom: 20px; font-size: 1.1em; }
    .filter-box { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #333; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- AI ANALYZER ---
def process_user_list(text):
    words = [w.strip() for w in text.replace(',', '\n').split('\n') if w.strip()]
    processed = {}
    bar = st.progress(0)
    for i, word in enumerate(words):
        try:
            tr = translator.translate(word, src='en', dest='tr').text.lower()
            dict_url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
            res = requests.get(dict_url, timeout=5)
            w_type, example = "noun", f"Study '{word}' for your exams."
            if res.status_code == 200:
                data = res.json()[0]
                w_type = data['meanings'][0]['partOfSpeech']
                for m in data['meanings']:
                    for d in m['definitions']:
                        if 'example' in d:
                            example = d['example']
                            break
            processed[word.lower()] = {"anlam": tr, "tur": w_type, "ornek": example, "seviye": "Custom", "kullanim": "User List"}
        except:
            processed[word.lower()] = {"anlam": word, "tur": "unknown", "ornek": "No details.", "seviye": "Custom", "kullanim": "N/A"}
        bar.progress((i + 1) / len(words))
    return processed

# --- SESSION STATE ---
if 'mode' not in st.session_state:
    st.session_state.update({
        'mode': 'menu', 'active_pool': {}, 'secilen': '', 
        'dogru': 0, 'yanlis': 0, 'gecmis': [], 'last_result': None
    })

# --- MENU SCREEN ---
if st.session_state.mode == "menu":
    st.title("👨‍✈️ FLIGHT CONTROL CENTER")
    
    tab1, tab2 = st.tabs(["📦 SYSTEM DATABASE", "📝 CUSTOM LIST"])
    
    with tab1:
        try:
            with open("kelime_veritabani.json", "r", encoding="utf-8") as f:
                full_db = json.load(f)
            
            st.markdown("<div class='filter-box'>", unsafe_allow_html=True)
            
            # --- FİLTRELEME MOTORU ---
            levels = sorted(list(set(v.get('seviye', 'B1') for v in full_db.values())))
            selected_levels = st.multiselect("Select Levels:", levels, default=levels)
            
            types = sorted(list(set(v.get('tur', 'noun') for v in full_db.values())))
            # Türlerin yanına sayı ekle
            type_options = {t: f"{t.capitalize()} ({len([x for x in full_db.values() if x.get('tur') == t and x.get('seviye') in selected_levels])})" for t in types}
            selected_types = st.multiselect("Select Types:", list(type_options.keys()), format_func=lambda x: type_options[x])
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            if st.button("🚀 START FLIGHT WITH FILTERS"):
                filtered = {k: v for k, v in full_db.items() if v.get('seviye') in selected_levels and v.get('tur') in selected_types}
                if filtered:
                    st.session_state.active_pool = filtered
                    st.session_state.mode = "flight"
                    st.rerun()
                else:
                    st.error("No words found matching these filters! Try adding more types/levels.")
        except:
            st.error("Database (kelime_veritabani.json) not found or empty!")

    with tab2:
        user_input = st.text_area("Paste words (comma or new line):", height=150)
        if st.button("ANALYSIS & START CUSTOM FLIGHT"):
            if user_input:
                with st.spinner("AI is analyzing your list..."):
                    st.session_state.active_pool = process_user_list(user_input)
                    st.session_state.mode = "flight"
                    st.rerun()

# --- FLIGHT (TEST) SCREEN ---
elif st.session_state.mode == "flight":
    if not st.session_state.secilen:
        st.session_state.secilen = random.choice(list(st.session_state.active_pool.keys()))
    
    target = st.session_state.active_pool[st.session_state.secilen]
    
    st.markdown(f"<div class='word-header'>{st.session_state.secilen.upper()}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='word-info'>{target.get('seviye', 'N/A')} | {target.get('tur', 'N/A')} | {target.get('kullanim', '')}</div>", unsafe_allow_html=True)

    # Audio
    tts = gTTS(text=st.session_state.secilen, lang='en')
    b = io.BytesIO(); tts.write_to_fp(b); st.audio(b.getvalue())

    if st.session_state.last_result:
        if "✅" in st.session_state.last_result: st.success(st.session_state.last_result)
        else:
            st.error(st.session_state.last_result)
            if st.button("⚠️ I actually knew this!"):
                st.session_state.dogru += 1; st.session_state.yanlis -= 1
                st.session_state.gecmis[-1]["Result"] = "✅ FIXED"
                st.session_state.last_result = "✅ Score Corrected!"
                st.rerun()

    with st.form(key='ans_form', clear_on_submit=True):
        ans = st.text_input("Translation:")
        if st.form_submit_button("CHECK ANSWER"):
            correct = target['anlam'].lower()
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

    if st.button("🏁 END FLIGHT"):
        st.session_state.mode = "report"
        st.rerun()

# --- REPORT SCREEN ---
else:
    st.title("🛬 FLIGHT SUMMARY")
    st.write(f"📊 **Final Stats:** {st.session_state.dogru} Correct / {st.session_state.yanlis} Wrong")
    st.table(pd.DataFrame(st.session_state.gecmis))
    if st.button("🔄 RETURN TO MENU"):
        for key in ['mode', 'active_pool', 'secilen', 'dogru', 'yanlis', 'gecmis', 'last_result']:
            st.session_state[key] = 'menu' if key == 'mode' else ({} if 'pool' in key else ([] if key == 'gecmis' else ''))
        st.rerun()
