import os
import requests
from urllib.parse import quote
import google.generativeai as genai
from dotenv import load_dotenv

# Çevre değişkenlerini yükle ve Gemini API'yi yapılandır
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

def configure_api(key):
    """
    API anahtarını dinamik olarak günceller.
    """
    global api_key
    api_key = key
    if key:
        genai.configure(api_key=key)

if api_key:
    configure_api(api_key)

def ask_gemini(prompt, system_instruction=None, image_data=None):
    """
    Doğrudan Gemini API'ye soru sorar. Görsel analizi destekler.
    image_data: {"mime_type": "...", "data": bytes}
    """
    if not api_key or not api_key.strip() or api_key.startswith("YOUR_GEMINI_API_KEY"):
        return "[HATA] Gemini API anahtarı yapılandırılmamış veya geçersiz. Lütfen sağ üstteki butona tıklayarak geçerli bir API anahtarı ekleyin."
    try:
        model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=system_instruction)
        if image_data and isinstance(image_data, dict):
            content = [
                {"mime_type": image_data.get("mime_type", "image/jpeg"), "data": image_data.get("data")},
                prompt
            ]
            response = model.generate_content(content)
        else:
            response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"[HATA] Gemini yanıt üretemedi: {str(e)}"

def web_search_and_summarize(query, system_instruction=None):
    """
    Wikipedia üzerinde arama yapar ve sonucu Gemini ile veya ham olarak döndürür.
    """
    headers = {
        "User-Agent": "JarvisBot/1.0 (burak@example.com) Python-Requests/2.33"
    }
    
    # 1. Türkçe Wikipedia üzerinde ara
    wiki_search_url = f"https://tr.wikipedia.org/w/api.php?action=query&list=search&srsearch={quote(query)}&format=json"
    
    try:
        res = requests.get(wiki_search_url, headers=headers, timeout=10)
        if res.status_code != 200:
            if api_key and not api_key.startswith("YOUR_GEMINI_API_KEY"):
                return ask_gemini(query, system_instruction=system_instruction), []
            return "[HATA] Wikipedia servisine bağlanılamadı ve Gemini API yapılandırılmamış.", []
            
        data = res.json()
        search_results = data.get("query", {}).get("search", [])
        
        if not search_results:
            # İngilizce Wikipedia araması dene (yedek olarak)
            en_search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={quote(query)}&format=json"
            res_en = requests.get(en_search_url, headers=headers, timeout=10)
            if res_en.status_code == 200:
                search_results = res_en.json().get("query", {}).get("search", [])
                is_turkish = False
            else:
                if api_key and not api_key.startswith("YOUR_GEMINI_API_KEY"):
                    return ask_gemini(query, system_instruction=system_instruction), []
                return "[JARVIS] Aradığınız konuya dair hiçbir Wikipedia sonucu bulunamadı (Gemini API aktif değil).", []
        else:
            is_turkish = True

        if not search_results:
            if api_key and not api_key.startswith("YOUR_GEMINI_API_KEY"):
                return ask_gemini(query, system_instruction=system_instruction), []
            return "[JARVIS] Aradığınız konuya dair hiçbir Wikipedia sonucu bulunamadı (Gemini API aktif değil).", []
            
        # En üstteki sonucu al
        top_result = search_results[0]
        title = top_result.get("title")
        
        # Sayfa detayını/özetini çek
        domain = "tr.wikipedia.org" if is_turkish else "en.wikipedia.org"
        extract_url = f"https://{domain}/w/api.php?action=query&prop=extracts&exintro&explaintext&titles={quote(title)}&format=json"
        
        res_extract = requests.get(extract_url, headers=headers, timeout=10)
        if res_extract.status_code != 200:
            if api_key and not api_key.startswith("YOUR_GEMINI_API_KEY"):
                return ask_gemini(query, system_instruction=system_instruction), []
            return "[HATA] Wikipedia sayfa detayları alınamadı ve Gemini API yapılandırılmamış.", []
            
        pages = res_extract.json().get("query", {}).get("pages", {})
        extract_text = ""
        for pid, pdata in pages.items():
            if "extract" in pdata:
                extract_text = pdata["extract"]
                break
                
        if not extract_text.strip():
            extract_text = top_result.get("snippet", "")
            
        # Kaynak linkini oluştur
        source_url = f"https://{domain}/wiki/{quote(title.replace(' ', '_'))}"
        sources = [(title, source_url)]
        
        # Eğer Gemini aktif değilse ham Wikipedia metnini döndür
        if not api_key or not api_key.strip() or api_key.startswith("YOUR_GEMINI_API_KEY"):
            prefix = "[WIKIPEDIA HIZLI ARAMA (Gemini Devre Dışı)]\n\n"
            return prefix + extract_text, sources
            
        # Gemini ile Wikipedia bilgisini kullanarak akıllıca cevap üret
        prompt = (
            f"Kullanıcı sorusu: '{query}'\n\n"
            f"Wikipedia kaynağı ({title}):\n{extract_text}\n\n"
            "Yukarıdaki kaynağı kullanarak kullanıcının sorusunu cevapla."
        )
        
        summary = ask_gemini(prompt, system_instruction=system_instruction)
        return summary, sources

    except Exception as e:
        if api_key and not api_key.startswith("YOUR_GEMINI_API_KEY"):
            return ask_gemini(query, system_instruction=system_instruction), []
        return f"[HATA] Arama sırasında bir sorun oluştu ve Gemini API devre dışı: {str(e)}", []
