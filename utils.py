import re
import csv

def get_category_by_hw_type(hw_model, hw_categories):
    model_type = re.search("[a-zA-Z]+", hw_model).group(0)
    for model_key, model_value in hw_categories.items():
        if (model_type in model_value):
            return model_key




def load_model_csv(filename):
    models = {}
    with open(filename) as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            models[row[0]] = row[1]
    return models