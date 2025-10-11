#!/usr/bin/env python3
import requests
import sys

try:
    response = requests.get('http://localhost:5000/time', timeout=2)
    if response.status_code == 200:
        data = response.json()
        print('Coordinator OK: Day', data['day'], '-', data['time_of_day'])
    else:
        print('Coordinator ERROR: HTTP', response.status_code)
except Exception as e:
    print('Coordinator ERROR:', e)

try:
    response = requests.get('http://localhost:5001/prices', timeout=2)
    if response.status_code == 200:
        data = response.json()
        print('Merchant OK:', len(data.get('buy_prices', {})), 'items')
    else:
        print('Merchant ERROR: HTTP', response.status_code)
except Exception as e:
    print('Merchant ERROR:', e)
