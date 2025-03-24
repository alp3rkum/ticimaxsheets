api_key = "CWQRWMFWTNA2PEOUFCBODIQS3TUHIG"
domain = "www.gokselgiyim.com"
file_name = 'MNG Kargo Verileri'
range_name = 'Sayfa2!A2:Z99999'

from ticiapi import select_siparis, siparis_data
from googlesheets import append_to_sheet, update_sheet
import datetime
import time
import logging
import json

logging.basicConfig(filename='hata.log', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

prev_orders = []

def main():
    global prev_orders
    siparisler = select_siparis(api_key,domain)
    for siparis in siparisler:    
        siparis_verileri = siparis_data(siparis)
        append_to_sheet(siparis_verileri,file_name,range_name)
        
    if prev_orders:
        updated_orders = get_updated_orders(prev_orders, siparisler)
        if updated_orders:
            update_sheet([siparis_data(order) for order in updated_orders], file_name, range_name)
        
    prev_orders = siparisler

def get_updated_orders(prev_orders, orders):
    prev_orders_dict = {(order['SiparisId'], order['UrunAdi']): order for order in prev_orders}
    print(f"Previous Orders Count: {len(prev_orders)}")
    updated_orders = []

    for order in orders:
        key = (order['SiparisId'], order['UrunAdi'])
        if key in prev_orders_dict:
            if order != prev_orders_dict[key]:
                updated_orders.append(order)
        else:
            updated_orders.append(order)
    
    return updated_orders


if __name__ == '__main__':
    while True:
        main()
        time.sleep(3600)