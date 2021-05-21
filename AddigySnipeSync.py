import os
import json
import pprint
import requests

# Load variables and secrets
from dotenv import load_dotenv
load_dotenv()

# Get all devices from Addigy
def load_addigy_devices():

    querystring = {'client_id': os.getenv(
        'ADDIGY_CLIENT_ID'), 'client_secret': os.getenv('ADDIGY_CLIENT_SECRET')}
    devices = requests.get(
        'https://prod.addigy.com/api/devices', params=querystring)
    data = devices.json()

    return data

def get_snipe_url():
    return os.getenv('SNIPE_BASE_URL')

def snipe_get_request(url):

    querystring = {"limit": "100", "offset": "0",
        "sort": "created_at", "order": "asc"}
    headers = {
        "Accept": "application/json",
        "Authorization": "Bearer " + os.getenv("SNIPE_TOKEN")
    }

    response = requests.request(
        "GET", get_snipe_url() + url, headers=headers, params=querystring)

    return response.json()


# Load all model types from Snipe IT
def load_snipe_models():
    return snipe_get_request("models")['rows']

def load_snipe_manufactuers():
    return snipe_get_request("manufacturers")['rows']

def load_snipe_categories():
    return snipe_get_request("categories")['rows']


def main():
    # Do all the things
    print("Running Main")

    models = set()
    data = load_addigy_devices()
    for device in data:
        device_model = device['Model and Year']
        if (device_model != None and len(device_model) > 0):
            models.add(device["Model and Year"])

    for model in models:
        print(model)

    models = load_snipe_models()
    pprint.pprint(models)


    # pprint.pprint(load_snipe_manufactuers())
    # pprint.pprint(load_snipe_categories())


    


if __name__ == "__main__":
    main()
