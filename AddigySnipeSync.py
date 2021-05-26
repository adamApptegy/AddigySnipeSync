import re
import csv
import html
import pprint
import addigy
import snipe


# Load variables and secrets
from dotenv import load_dotenv
load_dotenv(".env.prod")

hw_model_category_lookup = {
    "Laptop": ["MacBook", "MacBookPro", "MacBookAir"],
    "iMac": ["iMacPro", "iMac"],
    "Mac Mini": ["Macmini"],
    "iPad": ["iPad"],
    "Mobile Device": ["iPhone", "iPod"]
}





def get_category_by_hw_type(hw_model):
    model_type = re.search("[a-zA-Z]+", hw_model).group(0)
    for model_key, model_value in hw_model_category_lookup.items():
        if (model_type in model_value):
            return model_key




def load_model_csv(filename):
    models = {}
    with open(filename) as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            models[row[0]] = row[1]
    return models

def main():
    # Do all the things
    print("Running Main")

    model_lookup = load_model_csv("ModelID_Lookup.csv")

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

    if True:
        # Load Addigy Information
        devices = addigy.load_addigy_devices(False)

        # Do data processing

        seen_device_models = {}   


        for device in devices:
            #print(device['Serial Number'])
            #print(device['Product Name'] + " " + device['Product Description'])

            hw_model = device['Hardware Model']
            category = get_category_by_hw_type(hw_model)
            #print(category)
            

            category_id = category_dict[category]

            model_id = None

            device_descriptor = model_lookup[device['Hardware Model']]

            print(device['Hardware Model'] + "|" + model_lookup[device['Hardware Model']])

            if category != 'iPad' and category != 'Mac Mini':
                continue
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

                response = snipe.add_snipe_asset(status_id, model_id)
                if response is not None:
                    print("Added asset, updating")
                    # if it's successful, immediately  update the asset to add the serial number
                    snipe.update_snipe_asset(response['id'], device['Serial Number'])

            else:
                print("Asset Found with asset tag " + str(asset['asset_tag']) + ", updating")

                # we found the asset, if we want to update Addigy we can


            print() #print blank line


if __name__ == "__main__":
    main()
