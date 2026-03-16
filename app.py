import streamlit as st
import json
import random
import os
from gtts import gTTS
import io
import pandas as pd

st.set_page_config(page_title="Study-Buddy v3.9.8", page_icon="✈️")

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
    .report-card { background-color: #1a1a1a; padding: 20px; border-radius: 15px; border: 1px solid #00e676; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

def load_data():
    if os.path.exists("kelime_veritabani.json"):
        with open("kelime_veritabani.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# --- SESSION STATE ---
if 'kelime_listesi' not in st.session_state:
    st.session_state.kelime_listesi = load_data()
    st.session_state.aktif_havuz = list(st.session_state.kelime_listesi.keys())
    st.session_state.dogru = 0
    st.session_state.yanlis = 0
    st.session_state.secilen = ""
    st.session_state.last_result = None
    st.session_state.gecmis = []
    st.session_state.rapor_modu = False
    st.session_state.last_word_data = None # Düzeltme için son kelimeyi tutar

def soru_belirle():
    if not st.session_state.aktif_havuz:
        st.session_state.aktif_havuz = list(st.session_state.kelime_listesi.keys())
    weights = [st.session_state.kelime_listesi[k].get("oncelik", 100) for k in st.session_state.aktif_havuz]
    st.session_state.secilen = random.choices(st.session_state.aktif_havuz, weights=weights, k=1)[0]

if st.session_state.secilen == "" and not st.session_state.rapor_modu:
    soru_belirle()

# --- ANA EKRAN (SORU MODU) ---
if not st.session_state.rapor_modu:
    st.title("✈️ PILOT DASHBOARD v3.9.8")
    st.write(f"📊 **Skor:** {st.session_state.dogru} / {st.session_state.yanlis}")

    hedef = st.session_state.kelime_listesi[st.session_state.secilen]
    st.markdown(f"<h1>{st.session_state.secilen.upper()}</h1>", unsafe_allow_html=True)
    
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
        st.warning("⚠️ Audio engine error.")

    # --- SONUÇ VE DÜZELTME ALANI ---
    if st.session_state.last_result:
        if st.session_state.last_result.startswith("✅"):
            st.success(st.session_state.last_result)
        else:
            st.error(st.session_state.last_result)
            # Manuel Düzeltme Butonu (Sadece yanlış cevapta çıkar)
            if st.button("⚠️ I actually knew this! (Correction)"):
                st.session_state.dogru += 1
                st.session_state.yanlis -= 1
                # Son kaydı güncelle
                if st.session_state.gecmis:
                    st.session_state.gecmis[-1]["Durum"] = "✅ DÜZELTİLDİ"
                
                # Kelimeyi havuzdan çıkar (çünkü aslında bildi)
                if st.session_state.last_word_data in st.session_state.aktif_havuz:
                    st.session_state.aktif_havuz.remove(st.session_state.last_word_data)
                
                st.session_state.last_result = "✅ Correction applied!"
                st.rerun()

    def handle_submit():
        user_ans = st.session_state.ans_input.strip().lower()
        if not user_ans: return
        correct_ans = hedef['anlam'].lower()
        
        st.session_state.last_word_data = st.session_state.secilen # Düzeltme için sakla
        status = "✅ DOĞRU" if user_ans == correct_ans else "❌ YANLIŞ"
        
        st.session_state.gecmis.append({
            "Kelime": st.session_state.secilen.upper(),
            "Senin Cevabın": user_ans,
            "Doğru Anlam": correct_ans,
            "Durum": status
        })

        if user_ans == correct_ans:
            st.session_state.dogru += 1
            st.session_state.last_result = f"✅ DOĞRU! '{st.session_state.secilen}'"
            if st.session_state.secilen in st.session_state.aktif_havuz:
                st.session_state.aktif_havuz.remove(st.session_state.secilen)
        else:
            st.session_state.yanlis += 1
            st.session_state.last_result = f"❌ YANLIŞ! Doğrusu: {correct_ans.upper()}"
        soru_belirle()

    with st.form(key='fair_play_form', clear_on_submit=True):
        st.text_input("Meaning:", key="ans_input")
        st.form_submit_button(label='CHECK ANSWER', on_click=handle_submit)

    with st.expander("💡 HINT"):
        st.write(hedef.get('ornek', 'No hint.'))

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("NEXT WORD ➡️"):
            st.session_state.last_result = None
            soru_belirle()
            st.rerun()
    with col2:
        if st.button("🏁 FINISH & REPORT"):
            st.session_state.rapor_modu = True
            st.rerun()

# --- RAPOR EKRANI ---
else:
    st.title("🛬 FLIGHT SUMMARY")
    total = len(st.session_state.gecmis)
    if total > 0:
        accuracy = (st.session_state.dogru / total) * 100
        st.markdown(f"""
        <div class='report-card'>
            <h3>📈 Session Performance</h3>
            <p>Accuracy: <b>%{accuracy:.1f}</b></p>
            <p>Correct: <b style='color: #00e676;'>{st.session_state.dogru}</b> | Wrong: <b style='color: #ff5252;'>{st.session_state.yanlis}</b></p>
        </div>
        """, unsafe_allow_html=True)
        
        st.dataframe(pd.DataFrame(st.session_state.gecmis), use_container_width=True, hide_index=True)

    if st.button("🔄 START NEW FLIGHT"):
        st.session_state.rapor_modu = False
        st.session_state.gecmis = []
        st.session_state.dogru = 0
        st.session_state.yanlis = 0
        st.session_state.last_result = None
        soru_belirle()
        st.rerun()
