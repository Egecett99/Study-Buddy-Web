import streamlit as st
import json
import random
import os

# Sayfa Ayarları
st.set_page_config(page_title="Study-Buddy v3.6", page_icon="✈️")

# --- CSS: DARK MODE ---
st.markdown("""
    <style>
    .main { background-color: #101010; color: #00e676; }
    .stButton>button { width: 100%; background-color: #212121; color: #00e676; border: 1px solid #00e676; height: 3em; font-weight: bold; }
    .stTextInput>div>div>input { background-color: #1a1a1a; color: white; border: 1px solid #00e676; }
    h1, h2, h3 { color: #00e676 !important; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- VERİ YÜKLERKEN ÖNCELİK KONTROLÜ ---
def load_data():
    if os.path.exists("kelime_veritabani.json"):
        with open("kelime_veritabani.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            for k in data:
                if "oncelik" not in data[k]: data[k]["oncelik"] = 100
            return data
    return {}

# --- HAFIZA YÖNETİMİ ---
if 'kelime_listesi' not in st.session_state:
    st.session_state.kelime_listesi = load_data()
    st.session_state.aktif_havuz = list(st.session_state.kelime_listesi.keys())
    st.session_state.dogru = 0
    st.session_state.yanlis = 0
    st.session_state.secilen = ""
    st.session_state.last_result = None

# --- YENİ SORU SEÇME ---
def soru_belirle():
    if not st.session_state.aktif_havuz:
        st.session_state.aktif_havuz = list(st.session_state.kelime_listesi.keys())
    
    weights = [st.session_state.kelime_listesi[k].get("oncelik", 100) for k in st.session_state.aktif_havuz]
    st.session_state.secilen = random.choices(st.session_state.aktif_havuz, weights=weights, k=1)[0]

if st.session_state.secilen == "":
    soru_belirle()

# --- ARAYÜZ ---
st.title("✈️ PILOT DASHBOARD")
st.write(f"✅ Correct: {st.session_state.dogru} | ❌ Wrong: {st.session_state.yanlis} | 📦 Pool: {len(st.session_state.aktif_havuz)}")

# Mevcut Soru Paneli
st.markdown(f"<h1 style='font-size: 50px;'>{st.session_state.secilen.upper()}</h1>", unsafe_allow_html=True)
hedef = st.session_state.kelime_listesi[st.session_state.secilen]
st.write(f"Category: {hedef.get('tur', 'n/a')}")

# Sonuç Bildirimi (Bir önceki cevabın sonucunu burada gösteriyoruz)
if st.session_state.last_result:
    if st.session_state.last_result.startswith("✅"):
        st.success(st.session_state.last_result)
        st.balloons()
    else:
        st.error(st.session_state.last_result)

# Cevap Formu
def check_answer():
    user_ans = st.session_state.ans_input.strip().lower()
    correct_ans = hedef['anlam'].lower()
    
    if user_ans == correct_ans:
        st.session_state.dogru += 1
        st.session_state.last_result = f"✅ DOĞRU! '{st.session_state.secilen}' bildin."
        if st.session_state.secilen in st.session_state.aktif_havuz:
            st.session_state.aktif_havuz.remove(st.session_state.secilen)
        st.session_state.kelime_listesi[st.session_state.secilen]["oncelik"] = max(10, st.session_state.kelime_listesi[st.session_state.secilen].get("oncelik", 100) - 25)
    else:
        st.session_state.yanlis += 1
        st.session_state.last_result = f"❌ YANLIŞ! {st.session_state.secilen.upper()} = {correct_ans.upper()}"
        st.session_state.kelime_listesi[st.session_state.secilen]["oncelik"] = min(300, st.session_state.kelime_listesi[st.session_state.secilen].get("oncelik", 100) + 40)
    
    # Kelimeyi hemen değiştir
    soru_belirle()

st.text_input("Meaning:", key="ans_input", on_change=check_answer)
st.write("*(Type and press Enter)*")

with st.expander("💡 HINT"):
    st.write(hedef.get('ornek', 'No hint.'))

if st.button("NEXT WORD ➡️"):
    st.session_state.last_result = None
    soru_belirle()
    st.rerun()
