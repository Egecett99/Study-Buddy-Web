import json
import requests
from googletrans import Translator
import time

# Çeviri motorunu başlatıyoruz
translator = Translator()

def get_word_info(word):
    print(f"🔍 İşleniyor: {word}...")
    # Sözlük API adresi (Ücretsiz ve hızlıdır)
    dict_url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    
    try:
        # 1. Google üzerinden Türkçe anlamını çekiyoruz
        meaning_tr = translator.translate(word, src='en', dest='tr').text.lower()
        
        # 2. Sözlükten tür ve örnek cümle detaylarını çekiyoruz
        response = requests.get(dict_url)
        word_type = "unknown"
        example_en = "No example found."
        
        if response.status_code == 200:
            data = response.json()[0]
            # Kelime türünü al (Noun, Verb, Adjective)
            word_type = data['meanings'][0]['partOfSpeech']
            
            # Örnek cümle bulana kadar derinlere in
            found = False
            for meaning in data['meanings']:
                for definition in meaning['definitions']:
                    if 'example' in definition:
                        example_en = definition['example']
                        found = True
                        break
                if found: break
        
        return {
            "anlam": meaning_tr,
            "tur": word_type,
            "kullanim": "", # Burayı istersen sonra manuel doldurursun
            "ornek": example_en,
            "oncelik": 100,
            "sorulma": 0,
            "dogru": 0,
            "yanlis": 0
        }
    except Exception as e:
        print(f"❌ {word} sırasında hata oluştu: {e}")
        return None

# --- BURAYA KELİMELERİNİ EKLE ---
if __name__ == "__main__":
    # Hazırlık kitabından veya aklından geçen kelimeleri buraya ekle
    kelime_listesi = ["turbulence", "aerodynamics", "fuselage", "thrust", "cockpit"] 
    
    sonuc_veritabani = {}
    
    for kelime in kelime_listesi:
        bilgi = get_word_info(kelime)
        if bilgi:
            sonuc_veritabani[kelime] = bilgi
        time.sleep(1) # API'yi engellememek için 1 saniye bekle
    
    # Oluşan veriyi bir dosyaya kaydediyoruz
    with open("yeni_kelimeler.json", "w", encoding="utf-8") as f:
        json.dump(sonuc_veritabani, f, ensure_all_ascii=False, indent=4)
        
    print("\n✅ İŞLEM TAMAM! 'yeni_kelimeler.json' dosyan hazır.")
