import os
import json
import requests

# Get all devices from Addigy
def load_addigy_devices(local):
    if local:
        with open('data.json') as f:
            data = json.load(f)
        return data
    else:
        querystring = {'client_id': os.getenv(
            'ADDIGY_CLIENT_ID'), 'client_secret': os.getenv('ADDIGY_CLIENT_SECRET')}
        devices = requests.get(
            'https://prod.addigy.com/api/devices', params=querystring)
        data = devices.json()
        return data
