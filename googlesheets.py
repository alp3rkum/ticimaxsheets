import os
import pickle
import requests
import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import time

def load_credentials():
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
            return creds
    return None

def authenticate():
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    flow = InstalledAppFlow.from_client_secrets_file(
        'client_secret.json', SCOPES)
    creds = flow.run_local_server(port=0)
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)
    return creds

def get_services():
    creds = load_credentials()
    if not creds or not creds.valid:
        creds = authenticate()
    drive_service = build('drive', 'v3', credentials=creds)
    service = build('sheets', 'v4', credentials=creds)
    return service, drive_service

def get_or_create_sheet(service, drive_service, file_name, sheet_name):
    # Dosyayı ID'ye göre al
    file_id = None
    results = drive_service.files().list(q=f"name='{file_name}'", fields="files(id, name)").execute()
    items = results.get('files', [])
    if items:
        file_id = items[0]['id']

    if not file_id:
        print(f"Dosya '{file_name}' bulunamadı.")
        return None

    # Sayfayı aç
    spreadsheet = service.spreadsheets().get(spreadsheetId=file_id).execute()
    
    # Sayfanın var olup olmadığını kontrol et
    sheet_id = None
    for sheet in spreadsheet['sheets']:
        if sheet['properties']['title'] == sheet_name:
            sheet_id = sheet['properties']['sheetId']
            break

    # Sayfa yoksa oluştur
    if sheet_id is None:
        add_sheet_request = {
            "requests": [
                {
                    "addSheet": {
                        "properties": {
                            "title": sheet_name,
                            "gridProperties": {
                                "rowCount": 1000,
                                "columnCount": 60
                            }
                        }
                    }
                }
            ]
        }
        
        response = service.spreadsheets().batchUpdate(
            spreadsheetId=file_id,
            body=add_sheet_request
        ).execute()

        # Yeni oluşturulan sayfanın ID'sini al
        sheet_id = response['replies'][0]['addSheet']['properties']['sheetId']

        # Başlıkları yazma
        headers = ["Ürün Index","Sipariş No", "Sipariş Toplam Tutarı", "Ödeme Durumu", "Sipariş Kodu", "Stok Düştü", "Sipariş Durumu", "Paketleme Durumu",
                   "Düzenleme Tarihi", "Fatura Adresi", "Fatura İl", "Fatura İlçe", "Fatura Ülke", "Fatura Tel",
                   "Teslimat Adresi", "Teslimat İl", "Teslimat İlçe", "Teslimat Ülke", "Teslimat Tel", "Teslimat Tarih", "Ürün Adı",
                   "Ürün Adet", "Ürün Fiyatı", "Ürün Bedeni", "Stok Kodu", "Sipariş ID", "Ürün Resmi", "Üye Adı"]

        header_groups = [headers]
        
        for group_index, headers in enumerate(header_groups):
            body = {
                'requests': [
                    {
                        'updateCells': {
                            'rows': [
                                {
                                    'values': [
                                        {
                                            'userEnteredValue': {'stringValue': header},
                                            'userEnteredFormat': {
                                                'textFormat': {'bold': True}
                                            }
                                        } for header in headers
                                    ]
                                }
                            ],
                            'fields': 'userEnteredValue,userEnteredFormat.textFormat.bold',
                            'range': {
                                'sheetId': sheet_id,
                                'startRowIndex': 0,
                                'endRowIndex': 1,
                                'startColumnIndex': group_index * len(headers),
                                'endColumnIndex': (group_index + 1) * len(headers)
                            }
                        }
                    }
                ]
            }
            
            service.spreadsheets().batchUpdate(spreadsheetId=file_id, body=body).execute()
        
        print(f"{sheet_name} başarıyla oluşturuldu ve başlıklar eklendi.")
    else:
        print(f"{sheet_name} sayfası zaten mevcut.")
    
    return file_id

def get_existing_ids(service, spreadsheet_id, range_name):
    result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    values = result.get('values', [])
    existing_ids = set()
    
    # ID'leri bir set içinde toplayalım
    for row in values:
        existing_ids.add(row[22])

    return existing_ids

def append_to_sheet(values, file_name, range_name):
    service, drive_service = get_services()
    spreadsheet_id = get_or_create_sheet(service, drive_service,file_name,"Sayfa2")
    existing_ids = get_existing_ids(service, spreadsheet_id, range_name)
    
    new_values = []
    try:
        for veri in values:
            if f"{veri["SiparisID"]}" not in existing_ids:
                new_values.append(list(veri.values()))
        
        if new_values:
            new_values = convert_to_str(new_values)
            
            request = service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id, 
                range=range_name,
                valueInputOption="RAW", 
                body={"values": new_values}
            )
            response = request.execute()
            print(f"Google Sheets'e {len(new_values)} satır başarıyla eklendi.")
        else:
            print("Eklenmesi gereken yeni veri bulunamadı.")
    except:
        pass

def update_sheet(values, file_name, sheet_name, range_name):
    service, drive_service = get_services()
    spreadsheet_id = get_or_create_sheet(service, drive_service, file_name, sheet_name)
    
    if not spreadsheet_id:
        print("Spreadsheet ID bulunamadı.")
        return
    
    # Güncellenmesi gereken satırları belirle
    updates = []
    
    for index, row in enumerate(values):
        print(index)
        print(row)
        siparis_no = row[0]  # SiparisNo
        siparis_id = row[22]  # SiparisID
        urun_adi = row[17]  # UrunAdi
        stok_kodu = row[21]  # StokKodu
        updates.append({'siparis_no': siparis_no, 'siparis_id': siparis_id, 'urun_adi': urun_adi, 'stok_kodu': stok_kodu, 'row_data': row})
    
    # Mevcut verileri güncelle
    for update in updates:
        siparis_no = update['siparis_no']
        siparis_id = update['siparis_id']
        urun_adi = update['urun_adi']
        stok_kodu = update['stok_kodu']
        row_data = update['row_data']
        
        # Güncellenecek aralığı belirleme (örneğin: Sayfa2!A2:W2)
        range_to_update = range_name
        
        request = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range=range_to_update,
            valueInputOption="RAW", body={"values": [row_data]}
        )
        response = request.execute()
        print(f"Satır {siparis_no} - {siparis_id} - {urun_adi} - {stok_kodu} başarıyla güncellendi.")

def convert_to_str(values):
    for row in values:
        for i in range(len(row)):
            if isinstance(row[i], datetime.datetime):
                row[i] = row[i].strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(row[i], datetime.date):
                row[i] = row[i].strftime('%Y-%m-%d')
    return values