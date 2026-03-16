import sys
# Python 3.14 CGI Yaması
try:
    import cgi
except ImportError:
    try:
        import legacy_cgi as cgi
        sys.modules["cgi"] = cgi
    except ImportError:
        pass

import streamlit as st
import json
import random
import io
import pandas as pd
from gtts import gTTS
from googletrans import Translator

# --- SİSTEM AYARLARI ---
st.set_page_config(page_title="Study-Buddy v4.0", page_icon="✈️")
translator = Translator()

# --- CSS: PILOT UI ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #00e676; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; border: 1px solid #00e676; }
    .stTextArea>div>div>textarea { background-color: #1a1a1a; color: white; border: 1px solid #00e676; }
    .word-header { text-align: center; color: #00e676; font-size: 50px; margin-bottom: 0px; }
    .word-info { text-align: center; color: #888; margin-top: -10px; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- VERİ YÜKLEME (SENİN LİSTEN) ---
def load_fixed_data():
    try:
        with open("kelime_veritabani.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"aerodynamics": {"anlam": "aerodinamik", "tur": "noun", "ornek": "Aerodynamics is key in aviation.", "kullanim": "high speed"}}

# --- AI KELİME ANALİZCİSİ (KULLANICI LİSTESİ İÇİN) ---
def process_user_list(text):
    words = [w.strip() for w in text.replace(',', '\n').split('\n') if w.strip()]
    processed = {}
    bar = st.progress(0)
    for i, word in enumerate(words):
        try:
            # AI burada devreye giriyor
            tr = translator.translate(word, src='en', dest='tr').text.lower()
            processed[word.lower()] = {
                "anlam": tr,
                "tur": "detected",
                "ornek": f"Automated sentence for {word}.",
                "kullanim": "N/A"
            }
        except: continue
        bar.progress((i + 1) / len(words))
    return processed

# --- SESSION STATE ---
if 'mode' not in st.session_state:
    st.session_state.mode = "menu" # menu, flight, report
    st.session_state.active_pool = {}
    st.session_state.secilen = ""
    st.session_state.dogru = 0
    st.session_state.yanlis = 0
    st.session_state.gecmis = []

# --- MENU EKRANI ---
if st.session_state.mode == "menu":
    st.title("👨‍✈️ FLIGHT SELECTOR")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📦 Sabit Liste")
        st.write("Senin hazırladığın profesyonel kelime havuzu.")
        if st.button("SABİT LİSTE İLE BAŞLA"):
            st.session_state.active_pool = load_fixed_data()
            st.session_state.mode = "flight"
            st.rerun()

    with col2:
        st.subheader("📝 Kendi Listem")
        user_input = st.text_area("Kelimeleri buraya yapıştır:", placeholder="thrust, drag, lift...")
        if st.button("KENDİ LİSTEMİ OLUŞTUR"):
            if user_input:
                st.session_state.active_pool = process_user_list(user_input)
                st.session_state.mode = "flight"
                st.rerun()
            else: st.warning("Önce kelime ekle!")

# --- FLIGHT (TEST) EKRANI ---
elif st.session_state.mode == "flight":
    if not st.session_state.secilen:
        st.session_state.secilen = random.choice(list(st.session_state.active_pool.keys()))
    
    target = st.session_state.active_pool[st.session_state.secilen]
    
    st.markdown(f"<div class='word-header'>{st.session_state.secilen.upper()}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='word-info'>({target['tur']}) | {target.get('kullanim', '')}</div>", unsafe_allow_html=True)

    # Ses
    tts = gTTS(text=st.session_state.secilen, lang='en')
    b = io.BytesIO(); tts.write_to_fp(b)
    st.audio(b.getvalue())

    with st.form(key='q', clear_on_submit=True):
        ans = st.text_input("Anlamı nedir?")
        if st.form_submit_button("KONTROL ET"):
            correct = target['anlam'].lower()
            res = "✅ DOĞRU" if ans.strip().lower() == correct else "❌ YANLIŞ"
            st.session_state.gecmis.append({"Kelime": st.session_state.secilen, "Senin": ans, "Doğru": correct, "Sonuç": res})
            
            if "✅" in res: st.session_state.dogru += 1
            else: st.session_state.yanlis += 1
            
            st.session_state.secilen = random.choice(list(st.session_state.active_pool.keys()))
            st.rerun()

    with st.expander("💡 İPUCU (Örnek Cümle)"):
        st.write(target['ornek'])

    if st.button("🏁 UÇUŞU BİTİR"):
        st.session_state.mode = "report"
        st.rerun()

# --- RAPOR EKRANI ---
else:
    st.title("🛬 FLIGHT LOG")
    st.table(pd.DataFrame(st.session_state.gecmis))
    if st.button("🔄 ANA MENÜYE DÖN"):
        st.session_state.mode = "menu"
        st.session_state.secilen = ""
        st.session_state.gecmis = []
        st.rerun()
