import requests
import sys
import json
import os

import locale
locale.setlocale(locale.LC_ALL, '')  # Use '' for auto, or force e.g. to 'en_US.UTF-8'

#append the relative location you want to import from
sys.path.append("../includes")

#import your module stored in '../common'
import data_parser

sys.path.reverse()

api_key = "INSERT YOUR API KEY"
api_url = "https://api.api-ninjas.com/v1/country"

#tries to find an image for the entity and returns the object (if an image was found it will be append it to the object)
def add_image_property(obj, entity_name):
    absolute_path = os.path.dirname(__file__)
    relative_path = "../images/"
    target_path = os.path.join(absolute_path, relative_path)
    target_file_name = entity_name.lower()
    file_name = None
    if os.path.isfile(target_path + target_file_name + ".jpg"):
        file_name = target_file_name + ".jpg"
    if os.path.isfile(target_path + target_file_name + ".jpeg"):
        file_name = target_file_name + ".jpeg"
    if os.path.isfile(target_path + target_file_name + ".png"):
        file_name = target_file_name + ".png"
    if(file_name is not None):
        obj["_image"] = file_name
        print("Image found: "+ file_name)
    else:
        print("Image not found.")
    return obj

try:
    print("Country to fetch: ", end = "")
    input_str = input()

    while input_str:
        print("Fetching "+ input_str +"...")
        
        response = requests.get(api_url +"?name="+ input_str, headers={"X-Api-Key": api_key})
        if response.status_code == requests.codes.ok:
            data = response.json()[0]

            obj = {
                "population": f'{int(data["population"]) * 1000:,}',
                "urban_population": str(int(data["urban_population"])) + " %",
                "area": f'{int(data["surface_area"]):,}' + " km²",
                "gdp_per_capita": f'{int(data["gdp_per_capita"]):,}' + " USD",
                "unemployment": str(data["unemployment"]) + " %",
                "avg_life_expectancy": str(int((float(data["life_expectancy_male"]) + float(data["life_expectancy_female"])) / 2)) + " years",
                "internet_users": str(data["internet_users"]) + " %",
                "_labels": ["Population", "Urban population", "Area", "GDP per capita", "Unemployment", "Life expectancy", "Internet users"]
            }

            obj = add_image_property(obj, input_str)

            #saving data
            data_parser.save_single_data("Country", input_str, obj)
        else:
            print("Error:", response.status_code, response.text)

        print("Country to fetch: ", end = "")
        input_str = input()
except KeyboardInterrupt:
    sys.exit(0)