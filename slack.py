import requests
import json

def send_message(webhook_url, message):

    payload = {
        "text": message
    }
    return requests.post(webhook_url, json.dumps(payload))