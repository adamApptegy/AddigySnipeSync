import os
import re
import json
import html
import pprint
import requests

# Load variables and secrets
from dotenv import load_dotenv
load_dotenv()

LOCAL_JSON = True

hw_model_category_lookup = {
    "Laptop": ["MacBook", "MacBookPro", "MacBookAir"],
    "iMac": ["iMacPro", "iMac"],
    "Mac Mini": ["Macmini"],
    "Tablet": ["iPad"],
    "Mobile Device": ["iPhone", "iPod"]
}

# Get all devices from Addigy
def load_addigy_devices():
    if LOCAL_JSON:
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


def get_snipe_url():
    return os.getenv('SNIPE_BASE_URL')


def snipe_get_request(url, query_string="None"):

    if (query_string == "None"):
        querystring = {"limit": "100", "offset": "0",
                       "sort": "created_at", "order": "asc"}
    else:
        querystring = query_string

    headers = {
        "Accept": "application/json",
        "Authorization": "Bearer " + os.getenv("SNIPE_TOKEN")
    }

    response = requests.request(
        "GET", get_snipe_url() + url, headers=headers, params=querystring)

    return response.json()

def snipe_post_request(url, payload):

    headers = {
        "Accept": "application/json",
        "Authorization": "Bearer " + os.getenv("SNIPE_TOKEN")
    }

    response = requests.request(
        "POST", get_snipe_url() + url, headers=headers, json=payload)

    return response.json()

def snipe_put_request(url, payload):

    headers = {
        "Accept": "application/json",
        "Authorization": "Bearer " + os.getenv("SNIPE_TOKEN")
    }

    response = requests.request(
        "PUT", get_snipe_url() + url, headers=headers, json=payload)

    return response.json()

# Load all model types from Snipe IT
def load_snipe_models():
    return snipe_get_request("models")['rows']


def load_snipe_manufacturers():
    return snipe_get_request("manufacturers")['rows']


def load_snipe_categories():
    return snipe_get_request("categories")['rows']

def load_snipe_statuses():
    return snipe_get_request("statuslabels")['rows']


def get_category_by_hw_type(hw_model):
    model_type = re.search("[a-zA-Z]+", hw_model).group(0)
    for model_key, model_value in hw_model_category_lookup.items():
        if (model_type in model_value):
            return model_key


def load_snipe_assets(apple_manufacturer_id):
    querystring = {"limit": "100", "offset": "0",
                   "sort": "created_at", "order": "asc",
                   "manufacturer_id": apple_manufacturer_id}
    return snipe_get_request("hardware", querystring)['rows']

def get_snipe_asset_by_serial(serial_number, assets):
    #for asset in assets:
    # TODO: actually write this method
    for asset in assets:
        if asset['serial'] == serial_number:
            return asset
    return None

def get_snipe_status_id(statuses, status_name):
    for status in statuses:
        if status['name'] == status_name:
            return status['id']

def add_snipe_category(category):
    payload = {
            "use_default_eula": False,
        "require_acceptance": False,
        "checkin_email": False,
        "name": category,
        "category_type": "asset"
    }
    response = snipe_post_request("categories", payload)
    if response["status"] == "success":
        print("success")
        return response["payload"]
    else:
        pprint.pprint(response)
        return None

def add_snipe_model(model, category_id, manfuacturer_id):
    payload = {
        "name": model,
        "category_id": category_id,
        "manufacturer_id": manfuacturer_id
    }
    response = snipe_post_request("models", payload)
    if response["status"] == "success":
        print("success")
        return response["payload"]
    else:
        pprint.pprint(response)
        return None
def add_snipe_asset(status_id, model_id):
    payload = {
        "status_id": status_id,
        "model_id": model_id
    }
    response = snipe_post_request("hardware", payload)
    if response["status"] == "success":
        print("success")
        return response["payload"]
    else:
        pprint.pprint(response)
        return None

def update_snipe_asset(assetid, serial):
    payload = {
        "serial": serial
    }

    response = snipe_put_request("hardware/" + str(assetid), payload)
    if response["status"] == "success":
        return response["payload"]
    else:
        pprint.pprint(response)
        return None



def get_model(device):
    device_descriptor = ""
    if (device['Product Description'] != None):
        device_descriptor = device['Product Description']
    elif (device['Device Model Name'] != None):
        device_descriptor = device['Device Model Name']
    else:
        device_descriptor = device['Hardware Model']
    return device_descriptor

def main():
    # Do all the things
    print("Running Main")

    # Load Snipe-IT Information
    # Load Models
    models = load_snipe_models()
    print("Loaded " + str(len(models)) + " models")

    # Load Status Labels
    statuses = load_snipe_statuses()
    status_id = get_snipe_status_id(statuses, "Ready to Deploy")


    # Load Manufactuers
    manufacturers = load_snipe_manufacturers()

    print("Loaded " + str(len(manufacturers)) + " manufacturers")

    # Load Categories
    categories = load_snipe_categories()

    category_dict = {}

    print("Loaded " + str(len(categories)) + " categories")

    # Verify that all the categories exist within snipe that we're going to use
    # If they don't exist, create them
    for needed_category in hw_model_category_lookup.keys():
        found = False
        for category in categories:
            if category['name'] == needed_category:
                found = True

                category_dict[needed_category] = category['id']

                break
        
        if not found:
            print("didn't find category: " + needed_category)
            response = add_snipe_category(needed_category)
            if response != None:
                category_dict[needed_category] = response['id']
            else:
                print("something went wrong")

        

    # Find the correct manufacturer to associate apple devices with
    snipe_apple_manufacturer_id = None
    for manufacturer in manufacturers:
        if (manufacturer['name'] == 'Apple'):
            snipe_apple_manufacturer_id = manufacturer['id']

    if (snipe_apple_manufacturer_id == None):
        print("Error finding manufacturer Apple")
    else:
        print("Found manufacturer id for apple: " +
              str(snipe_apple_manufacturer_id))

    # Load Snipe asset information
    snipe_assets = load_snipe_assets(snipe_apple_manufacturer_id)

    if True:
        # Load Addigy Information
        devices = load_addigy_devices()

        # Do data processing

        # Go through all devices and see if there is a corresponding asset in Snipe-IT
        # If the value already exists, make sure all values are updated    
        # If the value does not exist, create it, find the asset tag that snipe-it created and feed that back to addigy

        seen_device_models = {}   

        count = 0

        for device in devices:
            count += 1
            if count > 10:
                break
            print(device['Serial Number'])
            # print(device['Product Name'] + " " + device['Product Description'])

            hw_model = device['Hardware Model']
            category = get_category_by_hw_type(hw_model)
            category_id = category_dict[category]

            model_id = None

            device_descriptor = get_model(device)
            # check if we've seen this model before
            if device_descriptor not in seen_device_models:
                print("Checking if new model exists in snipe")
                found = False
                for model in models:
                    if html.unescape(model['name']) == device_descriptor:
                        seen_device_models[device_descriptor] = model['id']
                        model_id = model['id']
                        found = True
                        break
                
                if not found:
                    print("Didn't find model for: " + device_descriptor)
                    # we haven't found the model in snipe so create it
                    response = add_snipe_model(device_descriptor, category_id, snipe_apple_manufacturer_id)
                    if response != None:
                        seen_device_models[device_descriptor] = response['id']
                        model_id = response['id']
                    else:
                        print("something went wrong")
            else:
                model_id = seen_device_models[device_descriptor]
            
            # Check if the device exists in snipe-it, use Serial number as common lookup
            asset = get_snipe_asset_by_serial(device['Serial Number'], snipe_assets)
            if asset is None:
                print("Asset not found, creating in Snipe-IT")
                
                

                # Need model id and status id to add device, but model_id needs category_id and manufacturer_id
                
                #print("Got status_id: " + str(status_id))

                response = add_snipe_asset(status_id, model_id)
                if response is not None:
                    print("Added asset, updating")
                    # if it's successful, immediately  update the asset to add the serial number
                    update_snipe_asset(response['id'], device['Serial Number'])

            else:
                print("Asset Found with asset tag " + str(asset['asset_tag']) + ", updating")

                # we found the asset, if we want to update Addigy we can


            print() #print blank line


if __name__ == "__main__":
    main()
