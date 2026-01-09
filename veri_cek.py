from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import json
import time

# --- AYARLAR ---
tum_urunler = []
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized") 
options.add_argument("--headless") 
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

print("🌍 Tarayıcı başlatılıyor...")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# --- SAYFA GEZME VE VERİ ALMA FONKSİYONU ---
def tablolari_gez_ve_al(kategori_adi, alt_liste_adi=""):
    sayfa_sayisi = 1
    
    while True:
        try:
            # Tabloyu bekle (Zaman aşımını 20 saniyeye çıkardık)
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//table//tbody//tr"))
            )
            time.sleep(2) # Sayfanın oturması için bekle

            satirlar = driver.find_elements(By.XPATH, "//table//tbody//tr")
            sayfa_verisi_sayisi = 0
            
            for satir in satirlar:
                hucreler = satir.find_elements(By.TAG_NAME, "td")
                if len(hucreler) > 1:
                    tum_urunler.append({
                        "firma": hucreler[0].text.strip(),
                        "urun": hucreler[1].text.strip(),
                        "marka": hucreler[2].text.strip(),
                        "sebep": hucreler[3].text.strip(),
                        "kategori": kategori_adi,
                        "alt_liste": alt_liste_adi
                    })
                    sayfa_verisi_sayisi += 1

            print(f"   📄 {alt_liste_adi} - Sayfa {sayfa_sayisi} okundu ({sayfa_verisi_sayisi} ürün).")

            # --- SONRAKİ BUTON KONTROLÜ ---
            sonraki_xpath = "//a[contains(text(), 'Sonraki')]"
            sonraki_btn = driver.find_elements(By.XPATH, sonraki_xpath)
            
            if len(sonraki_btn) > 0 and sonraki_btn[0].is_displayed():
                parent_class = sonraki_btn[0].find_element(By.XPATH, "./..").get_attribute("class")
                # Disabled kontrolü
                if "disabled" in str(parent_class):
                    print("   🛑 Son sayfaya gelindi.")
                    break
                else:
                    # Sonraki sayfaya git
                    driver.execute_script("arguments[0].click();", sonraki_btn[0])
                    sayfa_sayisi += 1
                    time.sleep(3) # Sayfa geçişi için bekle
            else:
                print("   🛑 Sonraki butonu yok, bitti.")
                break

        except Exception as e:
            print(f"   ⚠️ Döngü hatası: {e}")
            break

# =========================================================
# 1. ADIM: SAĞLIK TEHLİKESİ (Bu zaten çalışıyordu)
# =========================================================
try:
    print(f"\n🚀 [1/3] Sağlık Tehlikesi Listesi Çekiliyor...")
    driver.get("https://guvenilirgida.tarimorman.gov.tr/GuvenilirGida/gkd/SagligiTehlikeyeDusurecek?siteYayinDurumu=True")
    tablolari_gez_ve_al("Sağlık Tehlikesi")
except Exception as e:
    print(f"❌ Sağlık hatası: {e}")

# =========================================================
# 2. ADIM: TAKLİT/TAĞŞİŞ (ARKA KAPI YÖNTEMİ)
# =========================================================
# Butonlara tıklamak yerine, sitenin veriyi çektiği adreslere direkt gidiyoruz.
# Kaynak koddan bulduğumuz adresler:
taklit_urls = [
    {
        "ad": "Liste 1 (Taklit)",
        "url": "https://guvenilirgida.tarimorman.gov.tr/GuvenilirGida/GKD/TaklitVeyaTagsisListe1?modelType=model1&SiteYayinDurumu=True"
    },
    {
        "ad": "Liste 2 (Tağşiş)",
        "url": "https://guvenilirgida.tarimorman.gov.tr/GuvenilirGida/GKD/TaklitVeyaTagsisListe1?modelType=model2&SiteYayinDurumu=True"
    }
]

print(f"\n🚀 [2/3] Taklit ve Tağşiş Verileri Doğrudan Çekiliyor...")

for hedef in taklit_urls:
    try:
        print(f"   🔗 Bağlanılıyor: {hedef['ad']}")
        driver.get(hedef['url'])
        
        # Bu sayfalar sadece tablo içerir, header/footer olmayabilir. Bu robot için daha iyidir.
        tablolari_gez_ve_al("Taklit/Tağşiş", hedef['ad'])
        
    except Exception as e:
        print(f"   ❌ {hedef['ad']} hatası: {e}")

driver.quit()

# KAYDET
with open('yasakli_urunler.json', 'w', encoding='utf-8') as f:
    json.dump(tum_urunler, f, ensure_ascii=False, indent=4)

print(f"\n🎉 İŞLEM BİTTİ! Toplam {len(tum_urunler)} ürün kaydedildi.")