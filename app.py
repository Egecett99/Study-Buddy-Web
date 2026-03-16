import streamlit as st
import json
import random
import os
from gtts import gTTS
import io

st.set_page_config(page_title="Study-Buddy v3.9.5", page_icon="✈️")

# --- CSS: MODERN PILOT UI ---
st.markdown("""
    <style>
    .main { background-color: #101010; color: #00e676; }
    .stButton>button { width: 100%; background-color: #212121; color: #00e676; border: 1px solid #00e676; border-radius: 8px; font-weight: bold; }
    .stTextInput>div>div>input { background-color: #1a1a1a; color: white; border: 1px solid #00e676; border-radius: 8px; }
    h1 { color: #00e676 !important; text-align: center; margin-bottom: 5px; }
    .word-info { color: #757575; font-size: 16px; text-align: center; margin-top: -10px; margin-bottom: 20px; }
    .usage-tag { color: #ffa726; font-weight: bold; border: 1px solid #ffa726; padding: 2px 6px; border-radius: 4px; margin-left: 10px; font-size: 14px; }
    audio { width: 100%; height: 45px; margin-bottom: 20px; border-radius: 10px; filter: invert(1); }
    </style>
    """, unsafe_allow_html=True)

def load_data():
    if os.path.exists("kelime_veritabani.json"):
        with open("kelime_veritabani.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

if 'kelime_listesi' not in st.session_state:
    st.session_state.kelime_listesi = load_data()
    st.session_state.aktif_havuz = list(st.session_state.kelime_listesi.keys())
    st.session_state.dogru = 0
    st.session_state.yanlis = 0
    st.session_state.secilen = ""
    st.session_state.last_result = None

def soru_belirle():
    if not st.session_state.aktif_havuz:
        st.session_state.aktif_havuz = list(st.session_state.kelime_listesi.keys())
    weights = [st.session_state.kelime_listesi[k].get("oncelik", 100) for k in st.session_state.aktif_havuz]
    st.session_state.secilen = random.choices(st.session_state.aktif_havuz, weights=weights, k=1)[0]

if st.session_state.secilen == "":
    soru_belirle()

st.title("✈️ PILOT DASHBOARD v3.9.5")
st.write(f"📊 **Skor:** {st.session_state.dogru} / {st.session_state.yanlis} | 📦 **Pool:** {len(st.session_state.aktif_havuz)}")

hedef = st.session_state.kelime_listesi[st.session_state.secilen]
st.markdown(f"<h1>{st.session_state.secilen.upper()}</h1>", unsafe_allow_html=True)

# --- WORD INFO LINE (Type + Usage) ---
kullanim = hedef.get('kullanim', '')
usage_html = f"<span class='usage-tag'>Usage: {kullanim}</span>" if kullanim else ""
st.markdown(f"<div class='word-info'>({hedef.get('tur', 'unknown')}) {usage_html}</div>", unsafe_allow_html=True)

# Audio Engine
try:
    tts = gTTS(text=st.session_state.secilen, lang='en')
    audio_bytes = io.BytesIO()
    tts.write_to_fp(audio_bytes)
    st.audio(audio_bytes.getvalue(), format="audio/mpeg")
except:
    st.warning("⚠️ Audio engine warming up...")

if st.session_state.last_result:
    if st.session_state.last_result.startswith("✅"):
        st.success(st.session_state.last_result)
        st.balloons()
    else:
        st.error(st.session_state.last_result)

def handle_submit():
    user_ans = st.session_state.ans_input.strip().lower()
    if not user_ans: return
    correct_ans = hedef['anlam'].lower()
    if user_ans == correct_ans:
        st.session_state.dogru += 1
        st.session_state.last_result = f"✅ DOĞRU! '{st.session_state.secilen}'"
        if st.session_state.secilen in st.session_state.aktif_havuz:
            st.session_state.aktif_havuz.remove(st.session_state.secilen)
    else:
        st.session_state.yanlis += 1
        st.session_state.last_result = f"❌ YANLIŞ! Doğrusu: {correct_ans.upper()}"
    soru_belirle()

with st.form(key='colloc_form', clear_on_submit=True):
    st.text_input("Meaning:", key="ans_input")
    st.form_submit_button(label='CHECK ANSWER', on_click=handle_submit)

with st.expander("💡 HINT (Example Sentence)"):
    st.write(hedef.get('ornek', 'No example sentence.'))

if st.button("NEXT WORD ➡️"):
    st.session_state.last_result = None
    soru_belirle()
    st.rerun()
