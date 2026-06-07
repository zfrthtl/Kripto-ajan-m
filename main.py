import requests
import pandas as pd
import time

# --- TELEGRAM BİLGİLERİN ---
TELEGRAM_TOKEN = "8858292622:AAFMQCVbXfioESptybi9IZj143HNCGdhUh0"
TELEGRAM_CHAT_ID = "7138187423"

# --- AJANIN TAKİP EDECEĞİ KRİPTO PARALAR ---
TAKIP_LISTESI = ["BTC", "ETH", "SOL", "AVAX", "BNB", "DOGE", "XRP", "ADA", "TRX"]

def telegram_mesaj_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mesaj, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload, timeout=10)
    except: print("⚠️ Telegram mesajı gönderilemedi.")

def gecmis_verileri_getir(kripto):
    # 'histohour' kullanarak borsaların resmi 1 saatlik kapanış verilerini çekiyoruz
    url = f"https://min-api.cryptocompare.com/data/v2/histohour?fsym={kripto}&tsym=USDT&limit=24"
    response = requests.get(url).json()
    return pd.DataFrame(response['Data']['Data'])['close']

def rsi_hesapla(fiyatlar, periyot=14):
    kapanis_degisimi = fiyatlar.diff()
    kazanc = kapanis_degisimi.clip(lower=0)
    kayip = -1 * kapanis_degisimi.clip(upper=0)
    ema_kazanc = kazanc.ewm(com=periyot-1, adjust=False).mean()
    ema_kayip = kayip.ewm(com=periyot-1, adjust=False).mean()
    return (100 - (100 / (1 + (ema_kazanc / ema_kayip)))).iloc[-1]

# BAŞLANGIÇ AYARLARI
print(f"🤖 1 Saatlik Profesyonel Kripto Ajanı nöbette! Takiptekiler: {', '.join(TAKIP_LISTESI)}")
telegram_mesaj_gonder(f"🤖 *Profesyonel Kripto Ajanı Devrede (1 Saatlik Grafik)*\n\n🔍 Takip Listesi: `{', '.join(TAKIP_LISTESI)}` \n\nHer saat başında mum kapanışlarını inceleyip güçlü sinyaller arayacağım.")

# BOTUN HAFIZASI
son_sinyaller = {kripto: "BEKLE" for kripto in TAKIP_LISTESI}

# İLK ÇALIŞTIRMA (Açılışta kör kalmamak için hemen bir ilk tarama yapar)
print("🔄 İlk tarama başlatılıyor...")
for kripto in TAKIP_LISTESI:
    try:
        fiyat_serisi = gecmis_verileri_getir(kripto)
        guncel_rsi = rsi_hesapla(fiyat_serisi)
        if guncel_rsi <= 30: son_sinyaller[kripto] = "AL"
        elif guncel_rsi >= 70: son_sinyaller[kripto] = "SAT"
    except: pass

# 7/24 SAATLİK DÖNGÜ
while True:
    yerel_zaman = time.localtime()
    dakika = yerel_zaman.tm_min
    saniye = yerel_zaman.tm_sec
    
    # Sadece saat tam başında (Örn: 15:00:00) tarama yapar
    if dakika == 0 and saniye <= 10:
        print("-" * 50)
        print(f"⏰ Saatlik Mum Kapandı! Tarama Başlıyor: {time.strftime('%H:%M:%S')}")
        
        for kripto in TAKIP_LISTESI:
            try:
                fiyat_serisi = gecmis_verileri_getir(kripto)
                guncel_fiyat = fiyat_serisi.iloc[-1]
                guncel_rsi = rsi_hesapla(fiyat_serisi)
                
                if guncel_rsi <= 30: mevcut_sinyal = "AL"
                elif guncel_rsi >= 70: mevcut_sinyal = "SAT"
                else: mevcut_sinyal = "BEKLE"
                
                print(f"🪙 {kripto:4}: Fiyat: ${guncel_fiyat:,.2f} | 1H RSI: {guncel_rsi:.2f} | Durum: {mevcut_sinyal}")
                
                # Sinyal değiştiğinde telefona bildir
                if mevcut_sinyal != son_sinyaller[kripto]:
                    bildirim = f"📢 *1 SAATLİK GRAFİKTE YENİ SİNYAL* 📢\n🪙 *{kripto}/USDT*\n💵 Fiyat: ${guncel_fiyat:,.2f}\n📊 1H RSI: {guncel_rsi:.2f}\n"
                    if mevcut_sinyal == "AL": bildirim += "🟢 *GÜÇLÜ AL SİNYALİ OLUŞTU!*"
                    elif mevcut_sinyal == "SAT": bildirim += "🔴 *GÜÇLÜ SAT SİNYALİ OLUŞTU!*"
                    else: bildirim += f"🟡 {kripto} nötr bölgeye döndü, BEKLEME moduna geçildi."
                    
                    telegram_mesaj_gonder(bildirim)
                    son_sinyaller[kripto] = mevcut_sinyal
                    
            except Exception as e:
                print(f"⚠️ {kripto} taranırken hata: {e}")
            time.sleep(1)
            
        # Aynı saat içinde mükerrer tarama yapmaması için 15 saniye uyutuyoruz
        time.sleep(15)
        
    else:
        # Saat başı gelene kadar ekranda küçük bir sayaç gösterip kodu uykuda tutuyoruz
        print(f"💤 Saat başı bekleniyor... Şu anki Zaman: {time.strftime('%H:%M:%S')}", end="\r")
        time.sleep(10) # Her 10 saniyede bir saati kontrol eder
