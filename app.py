import streamlit as st
import json
import random
import os

# Sayfa Ayarları (Mobil Uyumluluk İçin)
st.set_page_config(page_title="Study-Buddy v3.5", page_icon="✈️", layout="centered")

# --- CSS: JARVIS DARK MODE ---
st.markdown("""
    <style>
    .main { background-color: #101010; color: #00e676; }
    .stButton>button { width: 100%; background-color: #212121; color: #00e676; border: 1px solid #00e676; border-radius: 10px; height: 3em; font-weight: bold; }
    .stTextInput>div>div>input { background-color: #1a1a1a; color: white; border: 1px solid #00e676; border-radius: 10px; }
    div[data-baseweb="toast"] { background-color: #1a1a1a; border: 1px solid #00e676; }
    h1, h2, h3 { color: #00e676 !important; font-family: 'Courier New', Courier, monospace; }
    </style>
    """, unsafe_allow_html=True)

# --- VERİ YÖNETİMİ ---
def load_data():
    if os.path.exists("kelime_veritabani.json"):
        with open("kelime_veritabani.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            # Öncelik sistemi yoksa ekle
            for k in data:
                if "oncelik" not in data[k]: data[k]["oncelik"] = 100
            return data
    return {}

# Session State (Verileri hafızada tutma)
if 'kelime_listesi' not in st.session_state:
    st.session_state.kelime_listesi = load_data()
    st.session_state.aktif_havuz = list(st.session_state.kelime_listesi.keys())
    st.session_state.dogru = 0
    st.session_state.yanlis = 0
    st.session_state.secilen = ""

# --- FONKSİYONLAR ---
def yeni_soru():
    if not st.session_state.aktif_havuz:
        st.session_state.aktif_havuz = list(st.session_state.kelime_listesi.keys())
    
    # Ağırlıklı Rastgele Seçim
    weights = [st.session_state.kelime_listesi[k].get("oncelik", 100) for k in st.session_state.aktif_havuz]
    st.session_state.secilen = random.choices(st.session_state.aktif_havuz, weights=weights, k=1)[0]

# --- ARAYÜZ ---
st.title("✈️ PILOT DASHBOARD v3.5")
st.write(f"📊 **Skor:** ✅ {st.session_state.dogru}  |  ❌ {st.session_state.yanlis}  |  📦 **Kalan:** {len(st.session_state.aktif_havuz)}")

# İlk soru yüklemesi
if not st.session_state.secilen:
    yeni_soru()

# Soru Paneli
st.subheader("Current Word:")
st.markdown(f"<h1 style='text-align: center; font-size: 60px;'>{st.session_state.secilen.upper()}</h1>", unsafe_allow_html=True)

hedef = st.session_state.kelime_listesi[st.session_state.secilen]
st.info(f"Part of Speech: {hedef.get('tur', 'n/a')}")

# Cevap Girişi (Form kullanarak enter takibini iyileştiriyoruz)
with st.form(key='answer_form', clear_on_submit=True):
    cevap = st.text_input("Meaning (Türkçe):").strip().lower()
    submit = st.form_submit_button("CHECK ANSWER")

if submit and cevap:
    dogru_cevap = hedef['anlam'].lower()
    if cevap == dogru_cevap:
        st.balloons()
        st.success(f"Perfect, Captain! '{st.session_state.secilen}' is removed from active pool.")
        st.session_state.dogru += 1
        if st.session_state.secilen in st.session_state.aktif_havuz:
            st.session_state.aktif_havuz.remove(st.session_state.secilen)
        # Önceliği düşür
        st.session_state.kelime_listesi[st.session_state.secilen]["oncelik"] = max(10, st.session_state.kelime_listesi[st.session_state.secilen].get("oncelik", 100) - 25)
        st.session_state.secilen = "" # Tetikle
        st.button("NEXT QUESTION ➡️")
    else:
        st.error(f"Wrong! Correct was: {dogru_cevap}")
        st.session_state.yanlis += 1
        # Önceliği artır
        st.session_state.kelime_listesi[st.session_state.secilen]["oncelik"] = min(300, st.session_state.kelime_listesi[st.session_state.secilen].get("oncelik", 100) + 40)
        st.session_state.secilen = ""
        st.button("TRY AGAIN ➡️")

# İpucu Alanı
with st.expander("💡 NEED A HINT?"):
    st.write(hedef.get('ornek', 'No example sentence provided.'))