# --- SIDEBAR: KELİME EKLEME (HANGAR) ---
with st.sidebar:
    st.header("🔧 Maintenance Hangar")
    st.subheader("Add Words (Single or List)")
    # İster tek kelime, ister virgüllü liste: "thrust, wing, pilot"
    input_text = st.text_area("Words:", placeholder="thrust, wing, velocity...").strip().lower()
    
    if st.button("🚀 ADD TO DATABASE"):
        if input_text:
            # Virgül veya yeni satıra göre kelimeleri ayır
            words_to_process = [w.strip() for w in input_text.replace(',', '\n').split('\n') if w.strip()]
            
            db = load_db()
            progress_bar = st.progress(0)
            
            for i, word in enumerate(words_to_process):
                with st.spinner(f"Processing: {word}..."):
                    try:
                        # Eğer kelime zaten varsa boşuna API yorma
                        if word not in db:
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
                        # Hata alsa bile anlamı çevirip ekle (en azından boş kalmasın)
                        db[word] = {"anlam": word, "tur": "unknown", "ornek": "Details not found.", "kullanim": "Error Recovery"}
                
                progress_bar.progress((i + 1) / len(words_to_process))
            
            save_db(db)
            st.success(f"Processed {len(words_to_process)} words!")
            st.rerun() # Sayıyı güncellemek için yenile
        else:
            st.warning("Write something first!")
