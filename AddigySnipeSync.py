import html
import pprint
from os.path import join, dirname
import snipe
import slack
import utils
import addigy
import json
import os

# Load variables and secrets
from dotenv import load_dotenv
load_dotenv(join(dirname(__file__), '.env'))

DRY_RUN = False

hw_model_category_lookup = {
    "Laptop": ["MacBook", "MacBookPro", "MacBookAir","Mac"],
    "iMac": ["iMacPro", "iMac"],
    "Mac Mini": ["Macmini"],
    "iPad": ["iPad"],
    "Mobile Device": ["iPhone", "iPod"],
    "Apple TV": [ "AppleTV" ]
}



def main():
    # Do all the things
    print("Running Main")



    model_lookup = utils.load_csv_key_value("ModelID_Lookup.csv")

    purchase_lookup = utils.load_csv_key_value("purchase-dates.csv")
    order_lookup = utils.load_csv_key_value("order-number.csv")

    # Load Snipe-IT Information
    # Load Models
    models = snipe.load_snipe_models()
    print("Loaded " + str(len(models)) + " models")

    # Load Status Labels
    statuses = snipe.load_snipe_statuses()
    status_id = snipe.get_snipe_status_id(statuses, "Ready to Deploy")


    # Load Manufactuers
    manufacturers = snipe.load_snipe_manufacturers()

    print("Loaded " + str(len(manufacturers)) + " manufacturers")

    # Load Categories
    categories = snipe.load_snipe_categories()

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
            response = snipe.add_snipe_category(needed_category)
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
    snipe_assets = snipe.load_snipe_assets(snipe_apple_manufacturer_id)

    print("Loaded " + str(len(snipe_assets)) + " snipe assets")

    if True:
        # Load Addigy Information
        devices = addigy.load_addigy_devices(False)
        
        # Do data processing

        seen_device_models = {}   


        for device in devices:
            print(device['Serial Number'])
            #print(device['Product Name'] + " " + device['Product Description'])

            hw_model = device['Hardware Model']
            print(hw_model)
            if hw_model is None:
                continue
            if "parallels" in hw_model.lower():
                print("Skipping because this is a VM!")
                continue
            
            if not device['Serial Number']: #some arbitrary number for now, fix this later
                print("Serial number doesn't look legit")
                #if there's no serial, skip it, since that's what we're matching on
                continue

            category = utils.get_category_by_hw_type(hw_model, hw_model_category_lookup)
            print(category)
            category_id = category_dict[category]

            model_id = None

            device_descriptor = model_lookup[device['Hardware Model']]

            print(device['Hardware Model'] + "|" + model_lookup[device['Hardware Model']])
            print(device['Serial Number'])
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
                    response = snipe.add_snipe_model(device_descriptor, category_id, snipe_apple_manufacturer_id)
                    if response != None:
                        seen_device_models[device_descriptor] = response['id']
                        model_id = response['id']
                    else:
                        print("something went wrong")
            else:
                model_id = seen_device_models[device_descriptor]
            
            # Check if the device exists in snipe-it, use Serial number as common lookup
            asset = snipe.get_snipe_asset_by_serial(device['Serial Number'], snipe_assets)
            if asset is None:
                print("Asset not found, creating in Snipe-IT")
                
                # Need model id and status id to add device, but model_id needs category_id and manufacturer_id
                
                #print("Got status_id: " + str(status_id))
                if not DRY_RUN:
                    response = snipe.add_snipe_asset(status_id, model_id)
                    if response is not None:
                        print("Added asset, updating")
                        # if it's successful, immediately  update the asset to add the serial number
                        snipe.update_snipe_asset(response['id'], device['Serial Number'])

                        #alert slack when a device is added

                        slack.send_message(os.getenv("SLACK_WEBHOOK"), f"*New asset added via Sync* \r\n*Model*: {device_descriptor}\r\n*Serial*: {device['Serial Number']} ")
                else:
                    print("Dry run: adding asset")
            else:
                print("Asset Found with asset tag " + str(asset['asset_tag']) + ", updating")
                # if you want to update or sync any fields between addigy and snipe, this would be a good time to do it.
                #pprint.pprint(asset)
                if asset['purchase_date'] is None:
                    print("attempting to add purchase date")
                    serial_number = asset['serial']
                    if serial_number in purchase_lookup.keys():
                        print(f"Updating purchase date for {asset['id']} to {purchase_lookup[serial_number]}")
                        snipe.update_purchase_date(asset['id'], purchase_lookup[serial_number])

                if asset['order_number'] is None:
                    print(f"attempting to add order number to {asset['order_number']}")
                    serial_number = asset['serial']
                    if serial_number in order_lookup.keys():
                        print(f"Updating order number for {asset['id']} to {order_lookup[serial_number]}")
                        snipe.update_order_number(asset['id'], order_lookup[serial_number])
                    
            print() #print blank line


if __name__ == "__main__":
    main()
