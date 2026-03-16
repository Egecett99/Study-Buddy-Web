import streamlit as st
import json
import random
import os

# Sayfa Ayarları
st.set_page_config(page_title="Study-Buddy v3.8", page_icon="✈️")

# --- CSS: MODERN PILOT UI ---
st.markdown("""
    <style>
    .main { background-color: #101010; color: #00e676; }
    .stButton>button { width: 100%; background-color: #212121; color: #00e676; border: 1px solid #00e676; border-radius: 8px; }
    .stTextInput>div>div>input { background-color: #1a1a1a; color: white; border: 1px solid #00e676; border-radius: 8px; }
    h1 { color: #00e676 !important; text-align: center; margin-bottom: 0px; }
    .word-type { color: #757575; font-style: italic; font-size: 18px; text-align: center; margin-top: -15px; margin-bottom: 20px; }
    .hint-box { background-color: #1a237e; color: white; padding: 10px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

def load_data():
    if os.path.exists("kelime_veritabani.json"):
        with open("kelime_veritabani.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data
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
    # Öncelik sistemi (basit rastgelelikten ağırlıklıya geçiş)
    weights = [st.session_state.kelime_listesi[k].get("oncelik", 100) for k in st.session_state.aktif_havuz]
    st.session_state.secilen = random.choices(st.session_state.aktif_havuz, weights=weights, k=1)[0]

if st.session_state.secilen == "":
    soru_belirle()

# --- ÜST BİLGİ PANELİ ---
st.title("✈️ STUDY-BUDDY PRO")
st.write(f"📊 **Skor:** {st.session_state.dogru} / {st.session_state.yanlis} | 📦 **Havuz:** {len(st.session_state.aktif_havuz)}")

# --- ANA SORU ALANI ---
hedef = st.session_state.kelime_listesi[st.session_state.secilen]

# Kelime Büyük ve Yeşil
st.markdown(f"<h1>{st.session_state.secilen.upper()}</h1>", unsafe_allow_html=True)
# Kelime Türü Küçük ve Soluk (İstediğin yer burası kanka)
st.markdown(f"<p class='word-type'>({hedef.get('tur', 'unknown')})</p>", unsafe_allow_html=True)

if st.session_state.last_result:
    if st.session_state.last_result.startswith("✅"):
        st.success(st.session_state.last_result)
        st.balloons()
    else:
        st.error(st.session_state.last_result)

# --- CEVAP ALANI ---
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

with st.form(key='study_form', clear_on_submit=True):
    st.text_input("Anlamını yaz:", key="ans_input")
    st.form_submit_button(label='KONTROL ET', on_click=handle_submit)

# --- İPUCU ALANI ---
with st.expander("💡 İPUCU (Örnek Cümle)"):
    # Eğer listede örnek cümle yoksa kullanıcıya hatırlatıyoruz
    ornek = hedef.get('ornek', '⚠️ Bu kelime için henüz örnek cümle eklenmemiş.')
    st.markdown(f"<div class='hint-box'>{ornek}</div>", unsafe_allow_html=True)

if st.button("SONRAKİ KELİME ➡️"):
    st.session_state.last_result = None
    soru_belirle()
    st.rerun()
