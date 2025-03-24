"""
Ticimax API Python Client
"""
from zeep import Client
from datetime import timedelta, datetime

def select_siparis(api_key, domain):
    # Servis URL'si
    wsdl = f'https://{domain}/Servis/SiparisServis.svc?wsdl'

    # Client oluşturma
    client = Client(wsdl=wsdl)

    # Bugünden itibaren 15 gün önceki tarih
    siparis_tarihi_bas = datetime.now() - timedelta(days=15)

    # WebSiparisFiltre nesnesi oluşturma
    webSiparisFiltre = {
        'EntegrasyonAktarildi': -1,
        'EntegrasyonParams': {
            'AlanDeger': '',
            'Deger': '',
            'EntegrasyonKodu': '',
            'EntegrasyonParamsAktif': True,
            'TabloAlan': '',
            'Tanim': ''
        },
        'IptalEdilmisUrunler': True,
        'FaturaNo': '',
        'OdemeDurumu': -1,
        'OdemeTipi': -1,
        'SiparisDurumu': -1,
        'SiparisID': -1,
        'SiparisKaynagi': '',
        'SiparisKodu': '',
        'SiparisTarihiBas': siparis_tarihi_bas,
        'SiparisTarihiSon': datetime.now(),  # Bitiş tarihi bugünün tarihi
        'StrSiparisDurumu': '',
        'TedarikciID': -1,
        'UyeID': -1,
        'SiparisNo': '',
        'UyeTelefon': ''
    }

    # WebSiparisSayfalama nesnesi oluşturma
    webSiparisSayfalama = {
        'BaslangicIndex': 0,
        'KayitSayisi': 100,
        'SiralamaDegeri': 'id',
        'SiralamaYonu': 'Desc'
    }

    # SelectSiparis metodunu çağırma
    response = client.service.SelectSiparis(
        UyeKodu=api_key,
        f=webSiparisFiltre,
        s=webSiparisSayfalama
    )

    return response

def siparis_data(siparis):
    siparis_verileri = []
    
    stok_dustu = siparis["StokDustu"]
    if stok_dustu == False:
        return
    
    siparis_no = siparis["SiparisNo"]
    siparis_toplam_tutar = siparis["SiparisToplamTutari"]
    odeme_durumu = "Durum Yok"
    if siparis:
        if siparis["Odemeler"] and siparis["Odemeler"]["WebSiparisOdeme"]:
            odeme_durumu = siparis["Odemeler"]["WebSiparisOdeme"][0]["Onaylandi"] if siparis["Odemeler"]["WebSiparisOdeme"][0] is not None else "Durum Yok"
    
    siparis_kodu = siparis['SiparisKodu']
    stok_dustu = siparis['StokDustu']
    siparis_durumu = siparis['SiparisDurumu']
    paketleme_durumu = siparis['PaketlemeDurumu']
    duzenleme_tarihi = siparis["DuzenlemeTarihi"]
        
    fatura_adresi = siparis["FaturaAdresi"]["Adres"]
    fatura_il = siparis["FaturaAdresi"]["Il"]
    fatura_ilce = siparis["FaturaAdresi"]["Ilce"]
    fatura_ulke = siparis["FaturaAdresi"]["Ulke"]["Tanim"]
    fatura_tel = siparis["FaturaAdresi"]["AliciTelefon"]
    
    teslimat_adresi = siparis["TeslimatAdresi"]["Adres"]
    teslimat_il = siparis["TeslimatAdresi"]["Il"]
    teslimat_ilce = siparis["TeslimatAdresi"]["Ilce"]
    teslimat_ulke = siparis["TeslimatAdresi"]["Ulke"]["Tanim"]
    teslimat_tel = siparis["TeslimatAdresi"]["AliciTelefon"]
    teslimat_tarih = siparis["TeslimatGunu"]
    uye_adi = siparis["UyeAdi"]
        
    urun_index = 0    
        
    for urun in siparis["Urunler"]["WebSiparisUrun"]:
        urun_index += 1
        urun_adi = urun["UrunAdi"]
        urun_adet = urun["Adet"]
        urun_fiyati = urun["Tutar"]
        urun_bedeni_listesi = urun['EkSecenekList']["WebSiparisUrunEkSecenekOzellik"]
        urun_bedeni = urun_bedeni_listesi[0]['Tanim'] if urun_bedeni_listesi else None
        stok_kodu = urun['StokKodu']
        siparis_id = urun['SiparisID']
        urun_resmi = urun['ResimYolu']

        
        urun_verisi = {
            "UrunIndex": urun_index,
            "SiparisNo": siparis_no,
            "SiparisToplamTutari": siparis_toplam_tutar,
            "OdemeDurumu": odeme_durumu,
            "SiparisKodu": siparis_kodu,
            "StokDustu": stok_dustu,
            "SiparisDurumu": siparis_durumu,
            "PaketlemeDurumu": paketleme_durumu,
            "DuzenlemeTarihi": duzenleme_tarihi,
            "FaturaAdresi": fatura_adresi,
            "FaturaIl": fatura_il,
            "FaturaIlce": fatura_ilce,
            "FaturaUlke": fatura_ulke,
            "FaturaTel": fatura_tel,
            "TeslimatAdresi": teslimat_adresi,
            "TeslimatIl": teslimat_il,
            "TeslimatIlce": teslimat_ilce,
            "TeslimatUlke": teslimat_ulke,
            "TeslimatTel": teslimat_tel,
            "TeslimatTarih": teslimat_tarih,
            "UyeAdi": uye_adi,
            "UrunAdi": urun_adi,
            "UrunAdet": urun_adet,
            "UrunFiyati": urun_fiyati,
            "UrunBedeni": urun_bedeni,
            "StokKodu": stok_kodu,
            "SiparisID": siparis_id,
            "UrunResmi": urun_resmi
        }

        siparis_verileri.append(urun_verisi)
    return siparis_verileri