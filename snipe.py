import os
import json
import pprint
import requests
from ratelimiter import RateLimiter


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

@RateLimiter(max_calls=100, period=60)
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

def load_snipe_assets(apple_manufacturer_id):
    current_page = 0
    page_limit = 100
    total = 9999999 # set this to a arbitrarily large value to start with, we'll get the total after the first page results
    devices = []

    while (current_page*page_limit) < total:
        #print(f"pulling page {current_page}")
        querystring = {"limit": str(page_limit), "offset": str(current_page*page_limit),
                "sort": "created_at", "order": "asc",
                "manufacturer_id": apple_manufacturer_id}
        result = snipe_get_request("hardware", querystring)
        total = result['total']
        devices.extend(result['rows'])
        current_page = current_page + 1
    
    return devices


def get_snipe_asset_by_serial(serial_number, assets):
    #for asset in assets:
    # TODO: actually write this method
    for asset in assets:
        if asset['serial'] == serial_number:
            return asset
    return None
def get_snipe_user_by_username(username):
    querystring={"username": username}
    resp = snipe_get_request("users", querystring)['rows']
    if len(resp) > 0:
        return resp[0]
    else:
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

def update_purchase_date(assetid, purchase_date):
    payload = {
        "purchase_date": purchase_date
    }

    response = snipe_put_request("hardware/" + str(assetid), payload)
    if response["status"] == "success":
        return response["payload"]
    else:
        pprint.pprint(response)
        return None

def update_order_number(assetid, order_number):
    payload = {
        "order_number": order_number
    }

    response = snipe_put_request("hardware/" + str(assetid), payload)
    if response["status"] == "success":
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
        
def assign_to_user(assetid, username):
    # get id of the user first
    user = get_snipe_user_by_username(username)

    if user is not None:
        userid = user["id"]
        payload = {
            'checkout_to_type': 'user',
            'assigned_user': userid
        }

        print("Attempting to assign to user: " + str(userid))
        snipe_post_request("hardware/" + str(assetid) + "/checkout", payload)
